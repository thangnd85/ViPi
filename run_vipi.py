''' 
crontab -e
# paste line to the end, press ctrl + X, Y. Then reboot Pi
@reboot python -u /home/pi/run_vipi.py
'''
import subprocess as s
import time, os
time.sleep(90)
cmd = "env/bin/python -u ./ViPi/src/main.py"
s.Popen(cmd, shell = True)
