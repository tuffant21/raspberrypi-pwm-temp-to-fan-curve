FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    nvme-cli \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir rpi-hardware-pwm

COPY fan_control.py .

CMD ["python", "-u", "fan_control.py"]