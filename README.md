# Raspberry Pi PWM Fan Monitor

## Introduction

Hello, thanks for checking out my repo. This repo is currently set up to only work for my setup. Please submit PRs to extend the functionality to work for yours too!

## My Setup

I am running a Raspberry Pi 5 with 16 gb of ram. I have Ubuntu 25.10 installed on my Pi, which may mean that my configuration may not work with vanilla raspian insallations.


## Prepare the Hardware PWM

The Raspberry Pi 5 requires a Device Tree Overlay to enable hardware PWM. 

1. Edit your config

```sh
sudo vim /boot/firmware/config.txt
```

2. Add these lines to the end of the file after the [all]:

```text
dtoverlay=pwm-2chan
dtparam=pin=12
dtparam=func=4
dtparam=pin2=18
dtparam=func2=2
```

3. Reboot your system

```sh
sudo reboot
```

### Debugging

If you need to debug the pins to see if they're running pwm mode, you can run these on ubuntu

```sh
sudo pinctrl get 18

# this should have this output
# 18: a3    pd | lo // GPIO18 = PWM0_CHAN2

sudo pinctrl get 12

# this should have this output
# 12: a0    pd | lo // GPIO12 = PWM0_CHAN0
```

If either of these do not show that they are using the pwm chan, you can to set them with these commands:
```sh
# Set Pin 12 to PWM mode (Alt 0)
sudo pinctrl set 12 a0
# Set Pin 18 to PWM mode (Alt 3)
sudo pinctrl set 18 a3

# Verify the settings
sudo pinctrl get 12,18
```

## Build the Dockerfile

```sh
docker build -t pi5-fan-control .
```

## Start the docker container

```sh
docker compose up -d
```

## Result

The fans should spin up at full speed when the application first boots. Then the fans should come down based on temps

## Changing Fan Curve

If you want to change the Fan Curve, edit the fan_control.py file. Change these variables to what you want.

```python
# Temperature Curve: (Celsius, Duty Cycle %)
TEMP_CURVE = [
    (34, 0),
    (35, 30),
    (40, 70),
    (45, 100)
]
```