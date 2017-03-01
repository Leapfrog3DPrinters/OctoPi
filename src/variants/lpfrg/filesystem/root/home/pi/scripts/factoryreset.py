#!/usr/bin/env python
# Author: Erik Heidstra <ErikHeidstra@live.nl>

import time
import RPi.GPIO as GPIO
import subprocess
import pygtk
import gtk, gobject, glib

FULLFACTORYRESETCOMMAND = r"echo 'full' | sudo tee /boot/factoryreset.txt && sudo sed -i 's@root=/dev/mmcblk0p2@root=/dev/mmcblk0p6@' /boot/cmdline.txt && sudo reboot"
FASTFACTORYRESETCOMMAND = r"echo 'fast' | sudo tee /boot/factoryreset.txt && sudo sed -i 's@root=/dev/mmcblk0p2@root=/dev/mmcblk0p6@' /boot/cmdline.txt && sudo reboot"

BUTTON_PIN = 16

BOUNCETIME = 100 # minimal press interval in ms
RESETPRESSTIME = 15 # duration of press before factory reset is initiated (in seconds)

RESPONSE_CANCEL=0
RESPONSE_FAST=1
RESPONSE_FULL=2

class PowerButtonHandler:
	def __init__(self):
		self.started = None
		self.ended = None
		self.confirmation_open = False

	def press_event(self, e):
		if GPIO.input(BUTTON_PIN):
			 # Interrupt the gtk main loop
			glib.idle_add(self.begin_press)
		else:
			# Interrupt the gtk main loop
			glib.idle_add(self.end_press)

	def begin_press(self):
		self.started = time.time()

	def end_press(self):
		self.ended = time.time()
		if not self.started:
			return

		if self.ended-self.started >= RESETPRESSTIME:
			self.confirm_factoryreset()

	def confirm_factoryreset(self):
		self.confirmation_open = True
		message = gtk.Dialog(buttons=("Cancel", RESPONSE_CANCEL, "Fast", RESPONSE_FAST, "Full", RESPONSE_FULL))
		message.set_default_size(400, 200)
		message.set_title("Factory reset")
		
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_DIALOG)

		label = gtk.Label("You are about to restore your printer to factory defaults. This will erase all your data. This action cannot be undone. You may choose for a fast restore or a full restore.\n\nWhich restore would you like to carry out?")
		label.set_line_wrap(True)

		content = message.get_content_area()
  		
  		box = gtk.HBox()
  		
		box.pack_start(image, True, True, 10)
		box.pack_start(label, True, True, 10)

		box.show()
		image.show()
		label.show()

		content.add(box)
		message.set_keep_above(True)
		response = message.run()
		self.confirmation_open = False
		message.destroy()
		
		if response == RESPONSE_FULL:
			subprocess.Popen(FULLFACTORYRESETCOMMAND, shell=True)
		elif response == RESPONSE_FAST:
			subprocess.Popen(FASTFACTORYRESETCOMMAND, shell=True)

pbh = PowerButtonHandler()
GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUTTON_PIN, GPIO.IN)
GPIO.add_event_detect(BUTTON_PIN, GPIO.BOTH, callback=pbh.press_event, bouncetime=BOUNCETIME)

glib.threads_init() 
gtk.main()