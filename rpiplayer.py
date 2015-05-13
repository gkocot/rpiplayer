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

#GPIO.output(led, GPIO.HIGH)

class KeyState(object):
	UP = 0
	DOWN = 1
	HOLD = 2


class KeyStruct(object):
	def __init__(self, id):
		self.id = id
		self.state = KeyState.UP
		self.time = 0


class Keyboard(object):
	def __init__(self):
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		#GPIO.setup(led, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)
		GPIO.setup([sw1, sw2, sw3, sw4], GPIO.IN, pull_up_down=GPIO.PUD_UP)
		#GPIO.add_event_detect(sw1, GPIO.BOTH, bouncetime=50)
		#GPIO.add_event_detect(sw2, GPIO.BOTH, bouncetime=50)
		#GPIO.add_event_detect(sw3, GPIO.BOTH, bouncetime=50)
		#GPIO.add_event_detect(sw4, GPIO.BOTH, bouncetime=50)
		
		self.keys = [KeyStruct(sw1), KeyStruct(sw2), KeyStruct(sw3), KeyStruct(sw4)]

	def process_keys(self):
		for i in range(len(self.keys)):
			id = self.keys[i].id
			state = self.keys[i].state
			
			if state == KeyState.UP:
				if not GPIO.input(id):
					self.keys[i].time = time.time()
					self.keys[i].state = KeyState.DOWN
					self.key_down(id)
			elif state == KeyState.DOWN:
				if GPIO.input(id):
					self.keys[i].state = KeyState.UP
					self.key_up(id)
					self.key_pressed(id)
				else:
					dt = time.time() - self.keys[i].time
					if dt > 3:
						self.keys[i].state = KeyState.HOLD
						self.key_hold(id)
					
			elif state == KeyState.HOLD:
				if GPIO.input(id):
					self.keys[i].state = KeyState.UP
					self.key_up(id)
			 
	def key_down(self, id):
		print '{0} key down'.format(id)

	def key_up(self, id):
		print '{0} key up'.format(id)

	def key_pressed(self, id):
		print '{0} key pressed'.format(id)
		
	def key_hold(self, id):
		print '{0} key held'.format(id)

"""			
		if GPIO.event_detected(sw1):
			print 'sw1={0}'.format(GPIO.input(sw1))
		if GPIO.event_detected(sw2):
			print 'sw2'
		if GPIO.event_detected(sw3):
			print 'sw3'
		if GPIO.event_detected(sw4):
			print 'sw4'
"""

k = Keyboard()
while True:
	k.process_keys()

		
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
