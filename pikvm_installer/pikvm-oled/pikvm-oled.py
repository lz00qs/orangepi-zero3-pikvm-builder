#!/usr/bin/env python3

import time
import subprocess

import board
import busio
import adafruit_ssd1306
from digitalio import DigitalInOut, Direction, Pull
from adafruit_blinka.microcontroller.allwinner.h616 import pin
from PIL import Image, ImageDraw, ImageFont

btn = DigitalInOut(board.PC11)
btn.direction = Direction.INPUT

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new("1", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)


# Draw a black filled box to clear the image.
def clear_image():
    draw.rectangle((0, 0, width, height), outline=0, fill=0)


# Load default font.
font = ImageFont.load_default(size=14)


# Clear display.
def clear_display():
    disp.fill(0)
    disp.show()


def is_kvmd_running():
    try:
        result = subprocess.run(["ps", "aux"], stdout=subprocess.PIPE)
        output = result.stdout.decode("utf-8")

        if "kvmd" in output:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking kvmd status: {e}")
        return False


def get_cpu_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temperature = int(file.read()) // 1000
            return temperature
    except Exception as e:
        print(f"Error getting CPU temperature: {e}")
        return None


def display_status():
    clear_image()
    # Shell scripts for system monitoring from here:
    # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    cmd = "hostname --ip-addresses"
    ip = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = 'cut -f 1 -d " " /proc/loadavg'
    load = subprocess.check_output(cmd, shell=True).decode("utf-8")
    cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB\", $3,$2 }'"
    MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")

    kvmd_status = "not running"
    if is_kvmd_running():
        kvmd_status = "running"

    cpu_temp = get_cpu_temperature()

    draw.text((0, 0), "IP: " + ip, font=font, fill=255)
    # draw.text((0, 15), "Load: " + CPU, font=font, fill=255)
    draw.text(
        (0, 15),
        "CPU: " + load.replace("\n", "") + " | " + str(cpu_temp) + "°C",
        font=font,
        fill=255,
    )
    draw.text((0, 30), MemUsage, font=font, fill=255)
    draw.text((0, 45), "KVMD: " + kvmd_status, font=font, fill=255)

    # Display image.
    disp.image(image)
    disp.show()


if __name__ == "__main__":
    try:
        loop_flag = True
        clear_display()
        while True:
            if btn.value:
                if not loop_flag:
                    loop_flag = True
            else:
                if loop_flag:
                    loop_flag = False
                    clear_display()
            if loop_flag:
                for i in range(0, 50):
                    display_status()
                    time.sleep(0.1)
                loop_flag = False
                clear_display()
    except Exception as e:
        print(f"Error: {e.to_string()}")
        clear_display()
    finally:
        clear_display()
