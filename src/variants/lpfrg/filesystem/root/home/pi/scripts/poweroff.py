#!/usr/bin/env python

COMMAND = "/usr/bin/sudo /sbin/shutdown -h now"
LED_PIN = 22 
PWR_PIN = 11 # Toggles power supply
BUTTON_PIN = 16

BOUNCETIME = 1000 # minimal press interval in ms

def callback(c):
    import subprocess
    subprocess.call(COMMAND.split())

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PWR_PIN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(BUTTON_PIN, GPIO.IN)

GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=callback, bouncetime=BOUNCETIME)

while 1:
	time.sleep(0.1)