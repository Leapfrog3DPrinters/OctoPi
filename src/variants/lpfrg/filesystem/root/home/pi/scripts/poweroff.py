#!/usr/bin/env python

COMMAND = "/usr/bin/sudo /sbin/shutdown -h now"
LED_PIN = 22 
PWR_PIN = 11 # Toggles power supply
BUTTON_PIN = 16

BOUNCETIME = 1000 # minimal press interval in ms
RESETPRESSTIME = 15 # maximum press duration for regular power off

def begin_press(e):
	started = time()

def end_press(e):
	ended = time()
	if not started:
		return

	if ended-started < RESETPRESSTIME:
		begin_shutdown()

def begin_shutdown():
	subprocess.call(COMMAND.split())

import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PWR_PIN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(BUTTON_PIN, GPIO.IN)

GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=begin_press, bouncetime=BOUNCETIME)
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=end_press, bouncetime=BOUNCETIME)


while 1:
    time.sleep(0.1)