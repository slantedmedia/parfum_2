import RPi.GPIO as GPIO
import time
import subprocess
import board
import neopixel
import os

# Exécuter aplay avec sudo en incluant les variables d'environnement nécessaires
def play_sound():
    command = "sudo aplay /home/pi/parfum_2/sound_fixed.wav"
    subprocess.Popen(command, shell=True, env={**os.environ, "DISPLAY": ":0", "XDG_RUNTIME_DIR": "/run/user/1000"})

# Configuration GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Configure GPIO17 avec pull-up interne
GPIO.setup(23, GPIO.OUT)  # Configure GPIO18 en sortie
GPIO.cleanup(23)

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
    GPIO.setup(23, GPIO.OUT)
    play_sound()
    time.sleep(5)  # Laisser actif 6 secondes
    GPIO.cleanup(23)

try:
    while True:
        if GPIO.input(17) == GPIO.LOW:
            handle_button_event(str(time.time()))
            time.sleep(2)  # Anti-rebond
        time.sleep(0.1)  # Pause pour économiser CPU
finally:
    GPIO.cleanup()  # Nettoyage général des GPIO
