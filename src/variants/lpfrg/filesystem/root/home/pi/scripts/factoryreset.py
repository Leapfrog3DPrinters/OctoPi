#!/usr/bin/env python
# Author: Erik Heidstra <ErikHeidstra@live.nl>

import time
import RPi.GPIO as GPIO
import subprocess
import pygtk
import gtk

FACTORYRESETCOMMAND = r"sudo sed -i 's@root=/dev/mmcblk0p2@root=/dev/mmcblk0p6@' /boot/cmdline.txt && sudo reboot"
BUTTON_PIN = 16

BOUNCETIME = 1000 # minimal press interval in ms
RESETPRESSTIME = 15 # duration of press before factory reset is initiated (in seconds)

confirmation_open = False
started = None
ended = None

def begin_press(e):
	started = time()

def end_press(e):
	ended = time()
	if not started:
		return

	if ended-started >= RESETPRESSTIME:
		confirm_factoryreset()

def confirm_factoryreset():
	#TODO: Maybe check if everything is set to open a confirmation dialog. If not, run the factory reset straight away
	confirmation_open = True
	message = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO)
	message.set_markup("You are about to reset your printer to factory defaults. This will erase all your data. Are you sure you want to continue? This action cannot be undone.")
	message.set_keep_above(True)
	response = message.run()
	confirmation_open = False
	message.destroy()

	if response == gtk.RESPONSE_YES:
		subprocess.Popen(FACTORYRESETCOMMAND, shell=True)


GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUTTON_PIN, GPIO.IN)
GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=begin_press, bouncetime=BOUNCETIME)
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=end_press, bouncetime=BOUNCETIME)

gtk.main()