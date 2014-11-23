import RPi.GPIO as GPIO
import subprocess

sw1 = 26
sw2 = 24
sw3 = 23
sw4 = 22
#led = 21


GPIO.setmode(GPIO.BOARD)
#GPIO.setup(led, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup([sw1, sw2, sw3, sw4], GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.setup(sw2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.setup(sw3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.setup(sw4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(sw1, GPIO.FALLING, bouncetime=200)
GPIO.add_event_detect(sw2, GPIO.FALLING, bouncetime=200)
GPIO.add_event_detect(sw3, GPIO.FALLING, bouncetime=200)
GPIO.add_event_detect(sw4, GPIO.FALLING, bouncetime=200)

#GPIO.output(led, GPIO.HIGH)

while True:
	if GPIO.event_detected(sw1):
		#subprocess.call(('mpc', 'next'))
		print "SW1"
	if GPIO.event_detected(sw2):
		print "SW2"
	if GPIO.event_detected(sw3):
                print "SW3"
	if GPIO.event_detected(sw4):
		subprocess.call(('mpc', 'next'))
                print "SW4"




