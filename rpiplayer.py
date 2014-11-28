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

def display():
	global fb_pos
	
	p = subprocess.Popen(['mpc', 'current'], stdout=subprocess.PIPE)
	current = p.communicate()[0].splitlines()[0].decode('windows-1252').encode('ascii', 'ignore')
	if current != framebuffer[1]:
		framebuffer[1] = current
		fb_pos = 0

	lcd.cursor_pos = (1, 0)
	if (len(framebuffer[1]) > 16):
		str = framebuffer[1][fb_pos : fb_pos + 16] + ' ' + framebuffer[1][:16]
		fb_pos = (fb_pos + 1) % len(framebuffer[1])
	else:
		str = framebuffer[1].ljust(16)
	
	lcd.write_string(str[:16])
	threading.Timer(1, display).start()

ip = subprocess.Popen(['ip', 'addr'], stdout=subprocess.PIPE)
grep1 = subprocess.Popen(['grep', 'inet.*brd', '-o'], stdout=subprocess.PIPE, stdin=ip.stdout)
grep2 = subprocess.Popen(['grep', '-E', '([0-9]{1,3}\.){3}[0-9]{1,3}', '-o'], stdout=subprocess.PIPE, stdin=grep1.stdout)
ip.stdout.close()
grep1.stdout.close()
framebuffer[0] = grep2.communicate()[0]
lcd.cursor_pos = (0, 0)
lcd.write_string(framebuffer[0][:16])

display()

while True:
	if GPIO.event_detected(sw1):
		print "SW1"
	if GPIO.event_detected(sw2):
		print "SW2"
	if GPIO.event_detected(sw3):
		subprocess.Popen(['mpc', 'prev'], stdout=subprocess.PIPE)
	if GPIO.event_detected(sw4):
		subprocess.Popen(['mpc', 'next'], stdout=subprocess.PIPE)

