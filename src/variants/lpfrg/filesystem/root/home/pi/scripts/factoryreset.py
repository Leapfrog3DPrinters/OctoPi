#!/usr/bin/env python

import time
import RPi.GPIO as GPIO
import subprocess
import pygtk
import gtk

COMMAND = r"sudo sed -i 's@root=/dev/mmcblk0p2@root=/dev/mmcblk0p3@' /boot/cmdline.txt && sudo reboot"

BUTTON_PIN = 16

BOUNCETIME = 1000 # minimal press interval in ms
PRESSTIME = 15000 # duration of press before factory reset is initiated

confirmation_open = False

def begin_press(e):
	if not confirmation_open:
		time.sleep(PRESSTIME) # Just wait around before checking if the button is still down
		if GPIO.input(BUTTON_PIN):
			confirm_factoryreset()


def confirm_factoryreset():
	confirmation_open = True
	message = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO)
	message.set_markup("You are about to reset your printer to factory defaults. This will erase all your data. Are you sure you want to continue? This action cannot be undone.")
	response = message.run()
	confirmation_open = False
	message.destroy()

	if response == gtk.RESPONSE_YES:
		subprocess.Popen(COMMAND, shell=True)


GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUTTON_PIN, GPIO.IN)
GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=begin_press, bouncetime=BOUNCETIME)

gtk.main()