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
num_pixels = 36
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, auto_write=False, pixel_order=neopixel.GRB)

pixels.fill((255, 255, 255))
pixels.show()

# Variables pour éviter les répétitions
last_event_time = 0
event_cooldown = 6
event_handled = set()

def handle_button_event(event_line):
    global last_event_time, event_handled
    if time.time() - last_event_time < event_cooldown:
        print("Délai de sécurité entre deux impulsions non respecté.")
        return
    if event_line in event_handled:
        print("Cet événement a déjà été traité.")
        return
    last_event_time = time.time()
    event_handled.add(event_line)

    print("Bouton pressé détecté ! Activation du diffuseur.")
    spiral_animation((255, 105, 180))  # Ajout de la couleur rose
    time.sleep(3.4)  # Laisser actif 3.4 secondes
    spiral_animation_remove()  # Correction ici aussi

# Fonction pour allumer en spirale
def spiral_animation(color, delay=0.05):
    for i in spiral_order:
        pixels[i] = color  # Allume LED
        pixels.show()
        time.sleep(delay)

# Fonction pour éteindre en spirale (inverse)
def spiral_animation_remove(delay=0.05):
    for i in reversed(spiral_order):  # Parcourt en sens inverse
        pixels[i] = (255, 255, 255)  # Éteint LED
        pixels.show()
        time.sleep(delay)

try:
    while True:
        if GPIO.input(17) == GPIO.LOW:
            handle_button_event(str(time.time()))
            time.sleep(2)  # Anti-rebond
        time.sleep(0.1)  # Pause pour économiser CPU
finally:
    GPIO.cleanup()  # Nettoyage général des GPIO
