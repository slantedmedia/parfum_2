import RPi.GPIO as GPIO
import time
import subprocess
import board
import neopixel
import os

spiral_order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]  

# Configuration GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Configure GPIO17 avec pull-up interne
GPIO.setup(4, GPIO.OUT, initial=GPIO.HIGH)  # GPIO4 en sortie, éteint au démarrage (relais inversé HIGH = OFF)

# Configuration des LEDs
pixel_pin = board.D21
num_pixels = 150
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, auto_write=False, pixel_order=neopixel.GRB)


num_pixels1 = 150
pixel_pin1 = board.D18
pixels1 = neopixel.NeoPixel(pixel_pin1, num_pixels1, brightness=0.1, auto_write=True, pixel_order=neopixel.GRB)


# LED sur GPIO 18 : reste toujours allumée
pixels1.fill((69, 201, 135))
pixels.fill((30, 180, 200))
pixels.show()

# Variables pour éviter les répétitions
last_event_time = 0
event_cooldown = 6

def handle_button_event():
    global last_event_time
    if time.time() - last_event_time < event_cooldown:
        print("Délai de sécurité entre deux impulsions non respecté.")
        return
    last_event_time = time.time()

    print("Bouton pressé détecté ! Activation du diffuseur.")
    GPIO.output(4, GPIO.LOW) # Courant ON sur GPIO4
    #pixels.fill((30, 180, 200))
    #pixels.show()
    time.sleep(5)
    #pixels.fill((0, 0, 0))
    #pixels.show()
    GPIO.output(4, GPIO.HIGH) # Courant OFF sur GPIO4

try:
    while True:
        if GPIO.input(17) == GPIO.LOW:
            handle_button_event()
            time.sleep(2)  # Anti-rebond
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Fin de programme")
finally:
    pixels.fill((0, 0, 0))
    #pixels.show()
    pixels1.fill((0, 0, 0))
    GPIO.output(4, GPIO.HIGH)
    GPIO.cleanup()