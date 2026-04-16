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

# Configuration des LEDs
pixel_pin = board.D21
num_pixels = 150
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, auto_write=False, pixel_order=neopixel.GRB)


# Variables pour éviter les répétitions
last_event_time = 0
event_cooldown = 6

def handle_button_event(event_line):
    global last_event_time
    if time.time() - last_event_time < event_cooldown:
        print("Délai de sécurité entre deux impulsions non respecté.")
        return
    last_event_time = time.time()

    print("Bouton pressé détecté ! Activation du diffuseur.")
    pixels.fill((208, 0, 111))  # Ajout de la couleur rose
    pixels.show()
    time.sleep(5)  # Laisser actif 3.4 secondes
    pixels.fill((0,0,0))
    pixels.show()

try:
    while True:
        if GPIO.input(17) == GPIO.LOW:
            handle_button_event(str(time.time()))
            time.sleep(2)  # Anti-rebond
        time.sleep(0.1)  # Pause pour économiser CPU
finally:
    GPIO.cleanup()  # Nettoyage général des GPIO