#!/bin/bash

alias octopy="/home/pi/OctoPrint/venv/bin/python"
alias octoinstall="octopy setup.py clean && octopy setup.py install"
alias octorestart="sudo service octoprint restart"
alias octoupdate="git pull && octoinstall && octorestart"
alias octolog="tail -f /home/pi/.octoprint/logs/octoprint.log"
alias octologn="tail /home/pi/.octoprint/logs/octoprint.log -n"
alias octoconfig="sudo nano /home/pi/.octoprint/config.yaml"