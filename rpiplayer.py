import RPi.GPIO as GPIO
from RPLCD import CharLCD
import subprocess
import threading
import time

sw1 = 22 # RANDOM
sw2 = 23 # PLAYLIST
sw3 = 26 # NEXT
sw4 = 24 # PREV
#led = 21

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
#GPIO.setup(led, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup([sw1, sw2, sw3, sw4], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(sw1, GPIO.FALLING, bouncetime=200)
GPIO.add_event_detect(sw2, GPIO.FALLING, bouncetime=200)
GPIO.add_event_detect(sw3, GPIO.FALLING, bouncetime=200)
GPIO.add_event_detect(sw4, GPIO.FALLING, bouncetime=200)
#GPIO.output(led, GPIO.HIGH)
lcd = CharLCD(pin_rs=11, pin_rw=7, pin_e=12, pins_data=[13, 15, 16, 18], cols=16, rows=2)

fb = ['', '']
fb_pos = [1, 1]
current_playlist_no=0
playlists = subprocess.Popen(['mpc', 'lsplaylists'], stdout=subprocess.PIPE).communicate()[0].splitlines()
random=False
subprocess.Popen(['mpc', 'random', 'off']).wait()

def get_ip_addr():
	ip = subprocess.Popen(['ip', 'addr'], stdout=subprocess.PIPE)
	grep1 = subprocess.Popen(['grep', 'inet.*brd', '-o'], stdout=subprocess.PIPE, stdin=ip.stdout)
	grep2 = subprocess.Popen(['grep', '-E', '([0-9]{1,3}\.){3}[0-9]{1,3}', '-o'], stdout=subprocess.PIPE, stdin=grep1.stdout)
	ip.stdout.close()
	grep1.stdout.close()
	return grep2.communicate()[0]

def display():
	global fb
	global fb_pos

	for line_no in range(0, 2):
		str = fb[line_no]
		if (len(str) > 16):
			str_display = (' ' + str)[fb_pos[line_no] : fb_pos[line_no] + 16] + (' ' + str[:16])
			fb_pos[line_no] = (fb_pos[line_no] + 1) % (len(str) + 1)
		else:
			str_display = str.ljust(16)
	
		lcd.cursor_pos = (line_no, 0)
		lcd.write_string(str_display[:16])

	threading.Timer(1, display).start()

def keyboard():
	global fb
	global fb_pos
	global random
	global current_playlist_no
	global playlists

	if GPIO.event_detected(sw1):
		random = not random
		if random:
			subprocess.Popen(['mpc', 'random', 'on']).wait()
			fb[0] = playlists[current_playlist_no][:15].ljust(15) + '*'
		else:
			subprocess.Popen(['mpc', 'random', 'off']).wait()
			fb[0] = playlists[current_playlist_no][:15].ljust(15) + ' '

	if GPIO.event_detected(sw2):
		current_playlist_no = (current_playlist_no + 1) % len(playlists)
		subprocess.Popen(['mpc', 'clear']).wait()
		subprocess.Popen(['mpc', 'load', playlists[current_playlist_no]]).wait()
		subprocess.Popen(['mpc', 'play', '1']).wait()
		fb[0] = playlists[current_playlist_no][:15].ljust(15) + ('*' if random else ' ')

	if GPIO.event_detected(sw3):
		subprocess.Popen(['mpc', 'prev']).wait()
	if GPIO.event_detected(sw4):
		subprocess.Popen(['mpc', 'next']).wait()
	
	p = subprocess.Popen(['mpc', 'current'], stdout=subprocess.PIPE)
	current = p.communicate()[0]
	if current:
		current = current.splitlines()[0].decode('windows-1252').encode('ascii', 'ignore')
	
	if current != fb[1]:
		fb[1] = current
		fb_pos[1] = 1

	threading.Timer(1, keyboard).start()

fb[0] = get_ip_addr()
keyboard()
display()

while True:
	ip = get_ip_addr()
	if not ip:
		fb[0] = 'network down'
		subprocess.Popen(['ifdown', 'wlan0']).wait()
		subprocess.Popen(['ifup', 'wlan0']).wait()
		ip = get_ip_addr()
		if ip:
			fb[0] = ip

	time.sleep(1)
