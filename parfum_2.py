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
PINS = {4, 17, 22, 24}

PULSE = 5  # duree de l'impulsion, en secondes

# Niveau applique sur la broche PENDANT l'impulsion. Depend de la carte relais :
#   carte a commande par la masse (la plus courante, marquee "LOW level trigger")
#       -> ACTIF = 0
#   carte a commande positive ("HIGH level trigger")
#       -> ACTIF = 1
# Au repos la broche est maintenue au niveau inverse, pas laissee flottante :
# une entree flottante derive et peut declencher le relais toute seule.
#
# Dans le doute, tester les deux : ACTIF = 0 puis ACTIF = 1, avec
#   sudo env/bin/python parfum_2.py --test 17
ACTIF = 1
REPOS = 1 - ACTIF
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
    # GPIO.output et pas seulement GPIO.setup(OUT) : sans ca la broche n'est
    # jamais pilotee et le relais ne voit aucun front. Les broches sont mises
    # en sortie une fois pour toutes au demarrage (voir main), et on ne fait
    # plus de cleanup par broche : ca la remettrait en entree flottante.
    GPIO.output(pin, ACTIF)
    time.sleep(PULSE)
    GPIO.output(pin, REPOS)
    leds((0, 0, 0))
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
    # Toutes les broches en sortie, au repos, des le demarrage : un relais ne
    # doit pas dependre de l'etat ou le boot a laisse la broche.
    for pin in sorted(PINS):
        GPIO.setup(pin, GPIO.OUT, initial=REPOS)
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


def test_broche(pin):
    """Une impulsion manuelle, sans tablette : sert a valider le cablage."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(pin, GPIO.OUT, initial=REPOS)
    print(f"GPIO{pin} : repos={REPOS}, impulsion a {ACTIF} pendant {PULSE}s...")
    try:
        GPIO.output(pin, ACTIF)
        time.sleep(PULSE)
        GPIO.output(pin, REPOS)
        print("Fini. Si le moteur n'a pas tourne, inverser ACTIF en tete du fichier.")
    finally:
        GPIO.cleanup(pin)


if __name__ == "__main__":
    if "--test" in sys.argv:
        test_broche(int(sys.argv[sys.argv.index("--test") + 1]))
        sys.exit(0)
    if "--selftest" in sys.argv:
        assert pin_de_ligne("I/kiosk(931): treeosk-btn-17 pressed") == 17
        assert pin_de_ligne("I/kiosk(931): treeosk-btn-04 pressed") == 4  # zero
        assert pin_de_ligne("D/wifi(12): scan results") is None
        assert pin_de_ligne("treeosk-btn-24") == 24  # ex-27, voir 802032c
        assert pin_de_ligne("treeosk-btn-27") is None  # hors liste blanche
        assert pin_de_ligne("treeosk-btn-") is None  # ligne tronquee
        assert {ACTIF, REPOS} == {0, 1}  # niveaux opposes, jamais les deux pareils
        print("selftest OK")
        sys.exit(0)
    main()
