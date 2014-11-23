import RPi.GPIO as GPIO
from RPLCD import CharLCD
import subprocess
import threading

sw1 = 26
sw2 = 24
sw3 = 23
sw4 = 22
#led = 21

GPIO.setmode(GPIO.BOARD)
#GPIO.setup(led, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup([sw1, sw2, sw3, sw4], GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(sw1, GPIO.FALLING, bouncetime=200)
GPIO.add_event_detect(sw2, GPIO.FALLING, bouncetime=200)
GPIO.add_event_detect(sw3, GPIO.FALLING, bouncetime=200)
GPIO.add_event_detect(sw4, GPIO.FALLING, bouncetime=200)
#GPIO.output(led, GPIO.HIGH)

framebuffer = [
	'radio',
	''
]

fb_pos = 0

lcd = CharLCD(pin_rs=11, pin_rw=7, pin_e=12, pins_data=[13, 15, 16, 18], cols=16, rows=2)

def write_to_lcd():
	#lcd.home()
	#for row in framebuffer:
	#	lcd.write_string(row.ljust(16)[:16])
	#	lcd.write_string('\r\n')
	lcd.cursor_pos = (0, 0)
	lcd.write_string(framebuffer[0].decode('windows-1252').encode('ascii', 'ignore').ljust(16)[:16])
	lcd.cursor_pos = (1, 0)
	lcd.write_string(framebuffer[1].decode('windows-1252').encode('ascii', 'ignore').ljust(16)[:16])

def scroll_lcd():
	threading.Timer(1, scroll_lcd).start()
	lcd.cursor_pos = (1, 0)
	if (len(framebuffer[1]) > 16):
		global fb_pos
		pos1 = fb_pos
		pos2 = (fb_pos + 16) % len(framebuffer[1])
		str1 = framebuffer[1][pos1 : pos1 + 16]
		str2 = framebuffer[1][pos2 : pos2 + 16]
		str = str1 + ' ' + str2
		fb_pos = (fb_pos + 1) % len(framebuffer[1])
	else:
		str = framebuffer[1].ljust(16)[:16]	
	lcd.write_string(str[:16])
	

framebuffer[1] = subprocess.Popen(['mpc', 'current'], stdout=subprocess.PIPE).communicate()[0].splitlines()[0]
#write_to_lcd()
scroll_lcd()

while True:
	if GPIO.event_detected(sw1):
		print "SW1"
	if GPIO.event_detected(sw2):
		print "SW2"
	if GPIO.event_detected(sw3):
		p = subprocess.Popen(['mpc', 'prev'], stdout=subprocess.PIPE)
		framebuffer[1] = p.communicate()[0].splitlines()[0].decode('windows-1252').encode('ascii', 'ignore')
		fb_pos = 0
		#scroll_lcd()
		#write_to_lcd()
	if GPIO.event_detected(sw4):
		p = subprocess.Popen(['mpc', 'next'], stdout=subprocess.PIPE)
		framebuffer[1] = p.communicate()[0].splitlines()[0].decode('windows-1252').encode('ascii', 'ignore')
		fb_pos = 0
		#scroll_lcd()
		#write_to_lcd()

