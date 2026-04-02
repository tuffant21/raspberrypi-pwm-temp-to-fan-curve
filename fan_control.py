import os
import time
import signal
import sys
import logging
import subprocess
import re
from rpi_hardware_pwm import HardwarePWM

# --- HARDWARE CONFIGURATION ---
# Confirmed via config.txt: dtoverlay=pwm-2chan,pin=12,func=4,pin2=18,func=3
# GPIO 12 -> PWM0_CHAN0 (chip 0, channel 0)
# GPIO 18 -> PWM0_CHAN2 (chip 0, channel 2)
FAN_CONFIGS = [
    {"chip": 0, "channel": 0, "label": "Fan 1 (GPIO 12)"},
    {"chip": 0, "channel": 2, "label": "Fan 2 (GPIO 18)"}
]

PWM_FREQ = 25000 

# Temperature Curve: (Celsius, Duty Cycle %)
TEMP_CURVE = [
    (34, 0),
    (35, 30),
    (40, 70),
    (45, 100)
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

class FanController:
    def __init__(self):
        self.pwms = []
        self._init_pwms()
        
    def _init_pwms(self):
        """Initialize PWM objects using the hardware-backed library."""
        for cfg in FAN_CONFIGS:
            try:
                pwm = HardwarePWM(pwm_channel=cfg["channel"], hz=PWM_FREQ, chip=cfg["chip"])
                pwm.start(0)
                self.pwms.append(pwm)
                logging.info(f"Initialized {cfg['label']} on chip{cfg['chip']}/pwm{cfg['channel']}")
            except Exception as e:
                logging.error(f"Failed to initialize {cfg['label']}: {e}")

        if not self.pwms:
            logging.error("No PWM channels could be opened. Check config.txt settings.")
            sys.exit(1)

        # Kickstart to ensure fans overcome static friction
        self.set_speed(100)
        time.sleep(2)

    def get_max_temp(self):
        """Read temperatures from CPU and NVMe devices."""
        temps = []
        # CPU
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temps.append(float(f.read()) / 1000.0)
        except Exception: pass
        
        # NVMe
        for dev in ['/dev/nvme0', '/dev/nvme0n1', '/dev/nvme1', '/dev/nvme1n1']:
            if os.path.exists(dev):
                try:
                    res = subprocess.run(['nvme', 'smart-log', dev], capture_output=True, text=True, timeout=1)
                    m = re.search(r'temperature\s*:\s*(\d+)\s*C', res.stdout, re.IGNORECASE)
                    if m: temps.append(float(m.group(1)))
                except Exception: pass
        
        return max(temps) if temps else 0.0

    def calculate_speed(self, temp):
        """Linear interpolation of fan speed based on TEMP_CURVE."""
        if temp <= TEMP_CURVE[0][0]: return 0.0
        if temp >= TEMP_CURVE[-1][0]: return 100.0
        for i in range(len(TEMP_CURVE) - 1):
            (t1, d1), (t2, d2) = TEMP_CURVE[i], TEMP_CURVE[i+1]
            if t1 <= temp <= t2:
                return d1 + (d2 - d1) * (temp - t1) / (t2 - t1)
        return 0.0

    def set_speed(self, percent):
        """Update all fans to the target percentage."""
        for pwm in self.pwms:
            try:
                pwm.change_duty_cycle(float(percent))
            except Exception: pass

    def stop(self):
        """Clean shutdown: stop fans and exit."""
        logging.info("Stopping fans and shutting down.")
        self.set_speed(0)
        for pwm in self.pwms:
            try:
                pwm.stop()
            except Exception: pass
        sys.exit(0)

    def run(self):
        logging.info("Fan controller loop started.")
        try:
            while True:
                t = self.get_max_temp()
                s = self.calculate_speed(t)
                logging.info(f"Temp: {t:.1f}C -> Fan Speed: {s:.1f}%")
                self.set_speed(s)
                time.sleep(10)
        except KeyboardInterrupt:
            self.stop()

if __name__ == "__main__":
    c = FanController()
    signal.signal(signal.SIGTERM, lambda s, f: c.stop())
    c.run()