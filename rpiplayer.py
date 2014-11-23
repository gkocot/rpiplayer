import RPi.GPIO as GPIO
from RPLCD import CharLCD
import subprocess

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


framebuffer[1] = subprocess.Popen(['mpc', 'current'], stdout=subprocess.PIPE).communicate()[0].splitlines()[0]
write_to_lcd()

while True:
	if GPIO.event_detected(sw1):
		print "SW1"
	if GPIO.event_detected(sw2):
		print "SW2"
	if GPIO.event_detected(sw3):
		framebuffer[1] = subprocess.Popen(['mpc', 'prev'], stdout=subprocess.PIPE).communicate()[0].splitlines()[0]
		write_to_lcd()
	if GPIO.event_detected(sw4):
		framebuffer[1] = subprocess.Popen(['mpc', 'next'], stdout=subprocess.PIPE).communicate()[0].splitlines()[0]
		write_to_lcd()




