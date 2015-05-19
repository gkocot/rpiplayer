import subprocess
import time
import RPi.GPIO as GPIO
from RPLCD import CharLCD


def get_ip_addr():
	ip = subprocess.Popen(['ip', 'addr'], stdout=subprocess.PIPE)
	grep1 = subprocess.Popen(['grep', 'inet.*brd', '-o'], stdout=subprocess.PIPE, stdin=ip.stdout)
	grep2 = subprocess.Popen(['grep', '-E', '([0-9]{1,3}\.){3}[0-9]{1,3}', '-o'], stdout=subprocess.PIPE, stdin=grep1.stdout)
	ip.stdout.close()
	grep1.stdout.close()
	return grep2.communicate()[0].rstrip()


class MPD(object):
	playlists = []
	current_playlist_no = 0
	random = False

	@staticmethod
	def init():
		MPD.playlists = subprocess.Popen(['mpc', 'lsplaylists'], stdout=subprocess.PIPE).communicate()[0].splitlines()
		subprocess.Popen(['mpc', 'clear']).wait()
		subprocess.Popen(['mpc', 'load', 'RADIO']).wait()
		subprocess.Popen(['mpc', 'random', 'off']).wait()
		subprocess.Popen(['mpc', 'repeat', 'on']).wait()
		subprocess.Popen(['mpc', 'volume', '100']).wait()
		subprocess.Popen(['mpc', 'play', '1']).wait()
		MPD.current_playlist_no = MPD.playlists.index('RADIO')

	@staticmethod
	def prev():
		subprocess.Popen(['mpc', 'prev']).wait()

	@staticmethod
	def next():
		subprocess.Popen(['mpc', 'next']).wait()

	@staticmethod
	def next_playlist():
			MPD.current_playlist_no = (MPD.current_playlist_no + 1) % len(MPD.playlists)
			subprocess.Popen(['mpc', 'clear']).wait()
			subprocess.Popen(['mpc', 'load', MPD.playlists[MPD.current_playlist_no]]).wait()
			subprocess.Popen(['mpc', 'play', '1']).wait()

	@staticmethod
	def get_current_playlist_name():
		return MPD.playlists[MPD.current_playlist_no]

	@staticmethod
	def get_current_stream_name():
		p = subprocess.Popen(['mpc', 'current'], stdout=subprocess.PIPE)
		current = p.communicate()[0]
		if current:
			current = current.splitlines()[0].decode('windows-1252').encode('ascii', 'ignore')
		return current

	@staticmethod
	def toggle_random():
		subprocess.Popen(['mpc', 'random']).wait()
		MPD.random = not MPD.random

MPD.init()


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
	sw1 = 22 # RANDOM
	sw2 = 23 # PLAYLIST
	sw3 = 26 # NEXT
	sw4 = 24 # PREV

	keys = [
		KeyStruct(sw1),
		KeyStruct(sw2),
		KeyStruct(sw3),
		KeyStruct(sw4)
	]
	
	KEY_HOLD_TIME = 2

	@staticmethod
	def init():
		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(Keyboard.sw1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(Keyboard.sw2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(Keyboard.sw3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(Keyboard.sw4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	@staticmethod
	def process_keys():
		for i in range(len(Keyboard.keys)):
			id = Keyboard.keys[i].id
			state = Keyboard.keys[i].state
			
			if state == KeyState.UP:
				if not GPIO.input(id):
					Keyboard.keys[i].time = time.time()
					Keyboard.keys[i].state = KeyState.DOWN
					Keyboard.key_down(id)
			elif state == KeyState.DOWN:
				if GPIO.input(id):
					Keyboard.keys[i].state = KeyState.UP
					Keyboard.key_up(id)
					Keyboard.key_pressed(id)
				else:
					dt = time.time() - Keyboard.keys[i].time
					if dt > Keyboard.KEY_HOLD_TIME:
						Keyboard.keys[i].state = KeyState.HOLD
						Keyboard.key_hold(id)
					
			elif state == KeyState.HOLD:
				if GPIO.input(id):
					Keyboard.keys[i].state = KeyState.UP
					Keyboard.key_up(id)
			
	@staticmethod
	def key_down(id):
		#print '{0} key down'.format(id)
		pass

	@staticmethod
	def key_up(id):
		#print '{0} key up'.format(id)
		pass

	@staticmethod
	def key_pressed(id):
		#print '{0} key pressed'.format(id)
		ScreenMgr.key_pressed(id)

	@staticmethod
	def key_hold(id):
		#print '{0} key held'.format(id)
		ScreenMgr.key_hold(id)


class LCD(object):
	ROWS = 2
	COLS = 16
	lcd = CharLCD(pin_rs=11, pin_rw=7, pin_e=12, pins_data=[13, 15, 16, 18], cols=COLS, rows=ROWS)

	@staticmethod
	def clear():
		for row in range(0, LCD.ROWS):
			LCD.write(row, 0, ' ' * LCD.COLS)
	
	@staticmethod
	def write(row, col, string):
		LCD.lcd.cursor_pos = (row, col)
		LCD.lcd.write_string(string.ljust(LCD.COLS)[:LCD.COLS])


class Screen(object):
	def get_text(self, row):
		pass

	def open(self):
		pass
	
	def close(self):
		pass
	
	def key_hold(self, id):
		pass
	
	def key_pressed(self, id):
		pass
	
	def refresh(self):
		pass


class TextScreen(Screen):
	def __init__(self, text):
		self.text = text
		
	def get_text(self, row):
		return self.text[row]


class PlayerScreen(Screen):
	def __init__(self):
		self.open()

	def get_text(self, row):
		if row == 0:
			str = MPD.get_current_playlist_name().ljust(LCD.COLS - 1)[:LCD.COLS - 1] + ('*' if MPD.random else ' ')
		else:
			str = MPD.get_current_stream_name()

		if (len(str) > LCD.COLS):
			return ' '.join([str, str])[self.pos[row]:self.pos[row] + LCD.COLS]
		else:
			return str

	def open(self):
		self.pos = [0, 0]
		self.time = time.time()
	
	def key_hold(self, id):
		if id == Keyboard.sw1:
			LCD.write(0, 0, 'Power OFF'.ljust(LCD.COLS))
			LCD.write(1, 0, ' ' * LCD.COLS)
			GPIO.cleanup()
			subprocess.Popen(['poweroff']).wait()
		elif id == Keyboard.sw2:
			MPD.toggle_random()

	def key_pressed(self, id):
		if id == Keyboard.sw2:
			MPD.next_playlist()
		elif id == Keyboard.sw3:
			MPD.prev()
		elif id == Keyboard.sw4:
			MPD.next()
		self.open()
	
	def refresh(self):
		if time.time() - self.time > 0.8:
			self.pos[0] = (self.pos[0] + 1) % (len(MPD.get_current_playlist_name()) + 1)
			self.pos[1] = (self.pos[1] + 1) % (len(MPD.get_current_stream_name()) + 1)
			self.time = time.time()


class ShowIPScreen(TextScreen):
	def __init__(self):
		super(ShowIPScreen, self).__init__(['IP Address', ''])

	def open(self):
		self.text[1] = get_ip_addr()


class ScreenMgr(object):
	screen = [
		PlayerScreen(),
		ShowIPScreen(),
	]

	current_screen = 0

	@staticmethod
	def refresh():
		ScreenMgr.screen[ScreenMgr.current_screen].refresh()
		LCD.write(0, 0, ScreenMgr.screen[ScreenMgr.current_screen].get_text(0).ljust(LCD.COLS)[:LCD.COLS])
		LCD.write(1, 0, ScreenMgr.screen[ScreenMgr.current_screen].get_text(1).ljust(LCD.COLS)[:LCD.COLS])
		
	@staticmethod
	def key_hold(id):		
		if id == Keyboard.sw3:
			ScreenMgr.screen[ScreenMgr.current_screen].close()
			ScreenMgr.current_screen = (ScreenMgr.current_screen + 1) % len(ScreenMgr.screen)
			ScreenMgr.screen[ScreenMgr.current_screen].open()
		else:
			ScreenMgr.screen[ScreenMgr.current_screen].key_hold(id)
			
	@staticmethod
	def key_pressed(id):
		ScreenMgr.screen[ScreenMgr.current_screen].key_pressed(id)


LCD.clear()
Keyboard.init()
while True:
	Keyboard.process_keys()
	ScreenMgr.refresh()
