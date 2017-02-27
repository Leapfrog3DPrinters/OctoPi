#!/usr/bin/env python
import RPi.GPIO as GPIO
import time

COMMAND = "/usr/bin/sudo /sbin/shutdown -h now"
LED_PIN = 22 
PWR_PIN = 11 # Toggles power supply
BUTTON_PIN = 16

BOUNCETIME = 100 # minimal press interval in ms
RESETPRESSTIME = 15 # maximum press duration for regular power off

class PowerButtonHandler:
	def __init__(self):
		self.started = None
		self.ended = None

	def press_event(self, e):
		if GPIO.input(BUTTON_PIN):
			self.begin_press()
		else:
			self.end_press()
			
	def begin_press(self):
		self.started = time.time()

	def end_press(self):
		self.ended = time.time()
		if not self.started:
			return

		if self.ended-self.started < RESETPRESSTIME:
			self.begin_shutdown()

	def begin_shutdown(self):
		subprocess.call(COMMAND.split())


GPIO.setmode(GPIO.BOARD)
GPIO.setup(PWR_PIN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(LED_PIN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(BUTTON_PIN, GPIO.IN)


pbh = PowerButtonHandler()
GPIO.add_event_detect(BUTTON_PIN, GPIO.BOTH, callback=pbh.press_event, bouncetime=BOUNCETIME)


while 1:
    time.sleep(0.1)