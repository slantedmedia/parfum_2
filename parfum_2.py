# -*- coding: utf-8 -*-
"""Ecoute la console d'une tablette Android branchee en USB (adb logcat).

Chaque ligne contenant "treeosk-btn-N" declenche une impulsion de PULSE
secondes sur le GPIO N (numerotation BCM), LEDs allumees pendant l'impulsion.

Le script se connecte tout seul : il attend la tablette au demarrage et se
reconnecte si on la debranche. Plus besoin d'attendre adb dans start_up.sh.
"""
import re
import subprocess
import sys
import time

try:
    import RPi.GPIO as GPIO
    import board
    import neopixel
except ImportError:  # machine de dev / --selftest
    GPIO = board = neopixel = None

# GPIO autorises a etre pulses depuis le log. Liste blanche volontaire :
# une ligne de log malformee ne doit pas pouvoir piloter n'importe quelle
# broche (I2C, SPI, l'alim des LEDs...). Ajouter un bouton = ajouter son GPIO.
PINS = {4, 17, 22, 27}

PULSE = 5  # duree de l'impulsion, en secondes
COOLDOWN = 2  # temps mini entre deux impulsions d'une meme broche

# "treeosk-btn-17" -> 17. Les zeros devant sont toleres (btn-04 == btn-4).
BTN = re.compile(r"treeosk-btn-0*(\d+)")

NUM_PIXELS = 100

pixels = None


def init_leds():
    global pixels
    pixels = neopixel.NeoPixel(board.D18, NUM_PIXELS, brightness=0.1,
                               auto_write=False, pixel_order=neopixel.GRB)
    leds((0, 0, 0))


def leds(couleur):
    pixels.fill(couleur)
    pixels.show()


def clear_logcat():
    """Vide le backlog : sans ca, la ligne qu'on vient de traiter peut
    reapparaitre et redeclencher l'impulsion."""
    subprocess.run(['adb', 'logcat', '-c'])


def pulse(pin):
    print(f"treeosk-btn-{pin} -> impulsion sur GPIO{pin}")
    leds((255, 255, 255))
    GPIO.setup(pin, GPIO.OUT)
    time.sleep(PULSE)
    leds((0, 0, 0))
    GPIO.cleanup(pin)
    clear_logcat()


def pin_de_ligne(ligne):
    """Ligne de log -> GPIO a pulser, ou None si rien a faire."""
    m = BTN.search(ligne)
    if not m:
        return None
    pin = int(m.group(1))
    return pin if pin in PINS else None


def ecoute():
    """Une session adb : attend la tablette, lit le log jusqu'a deconnexion."""
    # wait-for-device bloque tant qu'aucune tablette n'est branchee (et la
    # premiere commande adb demarre le serveur adb au passage).
    print("Attente de la tablette Android...")
    subprocess.run(['adb', 'wait-for-device'])
    clear_logcat()  # on ignore l'historique d'avant le demarrage
    proc = subprocess.Popen(['adb', 'logcat'], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True,
                            errors="replace")
    print("Connecte. Ecoute des evenements... CTRL+C pour arreter.")
    try:
        # readline et pas "for ligne in proc.stdout" : l'iteration bufferise
        # par blocs et les appuis arrivent en retard, par paquets.
        for ligne in iter(proc.stdout.readline, ""):
            pin = pin_de_ligne(ligne)
            if pin is None:
                continue
            if time.time() - dernier.get(pin, 0.0) < COOLDOWN:
                print("Ignore : appui trop rapproche.")
                continue
            dernier[pin] = time.time()
            pulse(pin)
    finally:
        proc.terminate()


dernier = {}  # GPIO -> horodatage de la derniere impulsion


def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    init_leds()
    try:
        while True:
            ecoute()
            # Sortie de boucle = tablette debranchee ou adb tue. On repart sur
            # wait-for-device, avec une pause pour ne pas tourner a vide.
            print("Tablette deconnectee, reconnexion...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Arret.")
    except FileNotFoundError:
        print("adb introuvable : sudo apt install -y adb")
    finally:
        leds((0, 0, 0))
        GPIO.cleanup()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        assert pin_de_ligne("I/kiosk(931): treeosk-btn-17 pressed") == 17
        assert pin_de_ligne("I/kiosk(931): treeosk-btn-04 pressed") == 4  # zero
        assert pin_de_ligne("D/wifi(12): scan results") is None
        assert pin_de_ligne("treeosk-btn-99") is None  # hors liste blanche
        assert pin_de_ligne("treeosk-btn-") is None  # ligne tronquee
        print("selftest OK")
        sys.exit(0)
    main()
