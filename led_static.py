import RPi.GPIO as GPIO
import time
import subprocess
import board
import neopixel
import os
 
spiral_order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
 
# Configuration GPIO
GPIO.setmode(GPIO.BCM)
#GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Configure GPIO17 avec pull-up interne
 
# Configuration des LEDs
# pixel_pin = board.D21
# num_pixels = 150
num_pixels1 = 150
# pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, auto_write=True, pixel_order=neopixel.GRB)
pixel_pin1 = board.D18
pixels1 = neopixel.NeoPixel(pixel_pin1, num_pixels1, brightness=0.1, auto_write=True, pixel_order=neopixel.GRB)
 
 
 
try:
        print("Bouton pressé détecté ! Activation du diffuseur.")
        # pixels.fill((208,0,111))
        pixels1.fill((208,0,111))
 
        while True:
            time.sleep(1)
 
 
except KeyboardInterrupt:
    print("Fin de programme")
