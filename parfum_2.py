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
num_pixels = 100
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
        process = subprocess.Popen(['adb', 'logcat'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Écoute des événements ADB... Appuyez sur CTRL+C pour arrêter.")

        button_event_pattern_17 = re.compile(r'.*treeosk-btn-17*')
        button_event_pattern_22 = re.compile(r'.*treeosk-btn-22*')
        button_event_pattern_27 = re.compile(r'.*treeosk-btn-27*')
        button_event_pattern_18 = re.compile(r'.*treeosk-btn-18*')

        while True:
            line = process.stdout.readline()
            if not line:
                break

            if button_event_pattern_17.search(line):
                print(f"Événement détecté : {line.strip()}")
                handle_button_event_17(line.strip())
            
            if button_event_pattern_22.search(line):
                print(f"Événement détecté : {line.strip()}")
                handle_button_event_22(line.strip())
            
            if button_event_pattern_27.search(line):
                print(f"Événement détecté : {line.strip()}")
                handle_button_event_27(line.strip())
                
            if button_event_pattern_18.search(line):
                print(f"Événement détecté : {line.strip()}")
                handle_button_event_18(line.strip())

    except KeyboardInterrupt:
        print("Arrêt de l'écoute des événements.")
    finally:
        # Arrête le processus adb logcat proprement
        process.terminate()
        GPIO.cleanup()  # Nettoyer les GPIO à la fin du script

def handle_button_event_17(event_line):
    global last_event_time, event_handled

    current_time = time.time()
    if current_time - last_event_time >= event_cooldown:
        if event_line not in event_handled:
            last_event_time = current_time  # Mettre à jour l'horodatage du dernier événement
            event_handled.add(event_line)  # Ajouter cet événement à l'ensemble des événements traités
            print("Bouton pressé détecté ! Vous pouvez ajouter une action ici.")
            print("Envoi d'une impulsion sur la broche 17...")
            pixels.fill((255, 240, 0))
            pixels.show()
            GPIO.setup(17, GPIO.OUT)  # Broche 17 configurée comme sortie
            time.sleep(5)
            pixels.fill((0, 0, 0))
            pixels.show()
            GPIO.cleanup(17)
            clear_logcat()

        else:
            print("Ignoré : L'événement a déjà été traité.")
    else:
        print("Ignoré : Appui détecté trop rapidement.")

def handle_button_event_18(event_line):
    global last_event_time, event_handled

    current_time = time.time()
    if current_time - last_event_time >= event_cooldown:
        if event_line not in event_handled:
            last_event_time = current_time  # Mettre à jour l'horodatage du dernier événement
            event_handled.add(event_line)  # Ajouter cet événement à l'ensemble des événements traités
            print("Bouton pressé détecté ! Vous pouvez ajouter une action ici.")
            print("Envoi d'une impulsion sur la broche 17...")
            pixels.fill((255, 240, 0))
            pixels.show()
            GPIO.setup(18, GPIO.OUT)  # Broche 17 configurée comme sortie
            time.sleep(5)
            pixels.fill((0, 0, 0))
            pixels.show()
            GPIO.cleanup(18)
            clear_logcat()

        else:
            print("Ignoré : L'événement a déjà été traité.")
    else:
        print("Ignoré : Appui détecté trop rapidement.")

def handle_button_event_22(event_line):
    global last_event_time, event_handled

    current_time = time.time()
    if current_time - last_event_time >= event_cooldown:
        if event_line not in event_handled:
            last_event_time = current_time  # Mettre à jour l'horodatage du dernier événement
            event_handled.add(event_line)  # Ajouter cet événement à l'ensemble des événements traités
            print("Bouton pressé détecté ! Vous pouvez ajouter une action ici.")
            print("Envoi d'une impulsion sur la broche 17...")
            pixels.fill((255, 240, 0))
            pixels.show()
            GPIO.setup(22, GPIO.OUT)  # Broche 17 configurée comme sortie
            time.sleep(5)
            pixels.fill((0, 0, 0))
            pixels.show()
            GPIO.cleanup(22)
            clear_logcat()

        else:
            print("Ignoré : L'événement a déjà été traité.")
    else:
        print("Ignoré : Appui détecté trop rapidement.")

def handle_button_event_27(event_line):
    global last_event_time, event_handled

    current_time = time.time()
    if current_time - last_event_time >= event_cooldown:
        if event_line not in event_handled:
            last_event_time = current_time  # Mettre à jour l'horodatage du dernier événement
            event_handled.add(event_line)  # Ajouter cet événement à l'ensemble des événements traités
            print("Bouton pressé détecté ! Vous pouvez ajouter une action ici.")
            print("Envoi d'une impulsion sur la broche 17...")
            pixels.fill((255, 240, 0))
            pixels.show()
            GPIO.setup(27, GPIO.OUT)  # Broche 17 configurée comme sortie
            time.sleep(5)
            pixels.fill((0, 0, 0))
            pixels.show()
            GPIO.cleanup(27)
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
