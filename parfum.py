import subprocess
import re
import RPi.GPIO as GPIO
import time
import board
import neopixel

# Configuration des GPIO
GPIO.setmode(GPIO.BCM)  # Mode BCM pour la numérotation des broches
GPIO.setwarnings(False)
pixel_pin = board.D18
num_pixels = 16
ORDER = neopixel.GRB
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, auto_write=False, pixel_order=ORDER)

pixels.fill((0, 0, 0))
pixels.show()

# Dernière détection pour éviter les répétitions
last_event_time = 0  # Stocke l'horodatage du dernier événement
event_cooldown = 2  # Temps minimum (en secondes) entre deux impulsions
event_handled = set()  # Ensemble pour mémoriser les événements traités

# Exécuter la commande adb logcat -c
def clear_logcat():
    try:
        subprocess.run(['adb', 'logcat', '-c'], check=True)
        print("Les logs ont été effacés avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande: {e}")

def listen_for_button_press():
    try:
        # Lance adb logcat pour écouter les logs du système
        process = subprocess.Popen(['adb', 'logcat'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Écoute des événements ADB... Appuyez sur CTRL+C pour arrêter.")

        # Expression régulière pour détecter un événement spécifique (modifiez selon vos besoins)
        button_event_pattern = re.compile(r'.*treeosk-btn-17.*')

        while True:
            line = process.stdout.readline()
            if not line:
                break

            # Vérifie si la ligne contient l'événement recherché
            if button_event_pattern.search(line):
                print(f"Événement détecté : {line.strip()}")
                handle_button_event(line.strip())  # Passer la ligne entière comme argument

    except KeyboardInterrupt:
        print("Arrêt de l'écoute des événements.")
    finally:
        # Arrête le processus adb logcat proprement
        process.terminate()
        GPIO.cleanup()  # Nettoyer les GPIO à la fin du script

def handle_button_event(event_line):
    global last_event_time, event_handled

    # Vérifie si suffisamment de temps s'est écoulé depuis le dernier événement
    current_time = time.time()
    if current_time - last_event_time >= event_cooldown:
        # Si l'événement n'a pas déjà été traité, nous le traitons
        if event_line not in event_handled:
            last_event_time = current_time  # Mettre à jour l'horodatage du dernier événement
            event_handled.add(event_line)  # Ajouter cet événement à l'ensemble des événements traités
            print("Bouton pressé détecté ! Vous pouvez ajouter une action ici.")
            print("Envoi d'une impulsion sur la broche 17...")
            pixels.fill((255, 160, 197))
            pixels.show()
            GPIO.setup(4, GPIO.OUT)  # Broche 17 configurée comme sortie
            time.sleep(9)
            pixels.fill((0, 0, 0))
            pixels.show()
            GPIO.cleanup(4)
            clear_logcat()

        else:
            print("Ignoré : L'événement a déjà été traité.")
    else:
        print("Ignoré : Appui détecté trop rapidement.")

def reset_event_handled():
    global event_handled
    # Réinitialiser l'ensemble des événements traités après un certain délai
    current_time = time.time()
    if current_time - last_event_time >= event_cooldown:
        event_handled.clear()  # Réinitialiser l'ensemble

if __name__ == "__main__":
    while True:
        listen_for_button_press()
        reset_event_handled()  # Réinitialise les événements après chaque boucle pour détecter les nouveaux événements
