import os
import subprocess
import sys
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None  # machine de dev / --selftest

# Dossier des sons, relatif a ce fichier : marche quel que soit l utilisateur
# (/home/pi/parfum_2 comme /home/treeosk/parfum_2) et depuis n importe quel cwd.
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
SHARED = f"{BASE}/T05.wav"  # boutons 5 a 9

# Broche BCM -> fichier son (boutons du telephone).
# Boutons 0-4 : un son chacun. Boutons 5-9 : T05.wav pour tous.
# NB: ces fichiers sont en Ogg malgre l'extension .wav -> ogg123 les lit, aplay non.
SOUNDS = {
    5: f"{BASE}/T00.wav",  # bouton 0
    6: f"{BASE}/T01.wav",  # bouton 1
    12: f"{BASE}/T02.wav",  # bouton 2
    13: f"{BASE}/T03.wav",  # bouton 3
    16: f"{BASE}/T04.wav",  # bouton 4
    19: SHARED,  # bouton 5
    20: SHARED,  # bouton 6
    24: SHARED,  # bouton 7
    25: SHARED,  # bouton 8
    26: SHARED,  # bouton 9
}

# Bouton stop : coupe le son en cours et n'en lance aucun. Cable comme les
# autres (broche -> bouton -> GND). Mettre None pour le desactiver.
STOP_PIN = 27

# Polarite du bouton stop.
# True  = repos HIGH, appui LOW (cablage normal vers GND, comme les 10 autres)
# False = repos LOW, appui HIGH (bouton normalement ferme / cable vers 3.3V)
# Si le son ne s'arrete qu'au relachement, c'est que cette valeur est inversee.
STOP_ACTIF_BAS = False

# ponytail: liste argv, pas shell=True et pas de sudo -- sinon terminate() tue le shell
# (ou sudo, qui ne transmet pas SIGTERM) et l'interruption du son ne marche pas.
# Le script tourne deja en root. Si ogg123 est muet mais paplay marche, changer cette ligne.
#
# ALSA_DEV : sortie audio forcee. Le defaut d'ALSA est souvent casse sur Pi
# ("Unknown PCM cards.pcm.front") -> on nomme la carte explicitement.
#
# Trouver la bonne valeur avec "aplay -l" (les numeros changent d'un Pi a l'autre) :
#   deux cartes -> carte 0 = HDMI, carte 1 = Headphones  => "plughw:1,0"
#   une carte   -> peri. 0 = jack, 1/2 = HDMI            => "plughw:0,0"
# Tester avant : sudo ogg123 -q -a plughw:1,0 sounds/T00.wav
#
# plughw et pas hw : hw exige le format exact du fichier et echoue sinon,
# plughw insere la conversion automatique.
# Mettre None pour laisser ALSA choisir.
ALSA_DEV = "plughw:2,0"

# Syntaxe ogg123 (man ogg123) : -d driver puis -o option:value.
# Le nom d'option du pilote alsa est "dev". Pas de -a (option inexistante),
# pas de "dev=" (c'est bien deux-points).
# Si le peripherique n'existe pas, ogg123 affiche "Cannot open <dev>" puis
# retombe sur le defaut ALSA "front" qui n'existe pas sur Pi -> les deux
# erreurs apparaissent ensemble.
PLAYER = ["ogg123", "-q"] + (["-d", "alsa", "-o", f"dev:{ALSA_DEV}"] if ALSA_DEV else [])

# Pas de env= : ogg123 parle directement a ALSA en root. L'ancien DISPLAY /
# XDG_RUNTIME_DIR servait uniquement a PulseAudio sous sudo.

DEBOUNCE = 0.25

current = None


def transitions(prev, cur):
    """Broches passees de HIGH a LOW (appui). Pure -> testable."""
    return [p for p in cur if cur[p] == 0 and prev.get(p, 1) == 1]


def stop():
    """Coupe le son en cours s'il y en a un. Sans effet sinon."""
    global current
    if current and current.poll() is None:
        current.terminate()
        current.wait()  # recupere le process, evite les zombies
    current = None


def play(pin):
    global current
    path = SOUNDS[pin]
    if not os.path.exists(path):
        print(f"Fichier manquant: {path}")
        return
    stop()  # le nouvel appui interrompt le son precedent
    print(f"GPIO{pin} -> {os.path.basename(path)}")
    current = subprocess.Popen(PLAYER + [path])


def main():
    # Toutes les broches surveillees : les sons + le bouton stop.
    broches = list(SOUNDS) + ([STOP_PIN] if STOP_PIN else [])

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in SOUNDS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    if STOP_PIN:
        # Pull oppose a l'etat de repos, sinon la broche flotte.
        GPIO.setup(STOP_PIN, GPIO.IN,
                   pull_up_down=GPIO.PUD_UP if STOP_ACTIF_BAS else GPIO.PUD_DOWN)

    for path in sorted(set(SOUNDS.values())):
        if not os.path.exists(path):
            print(f"ATTENTION fichier manquant au demarrage: {path}")

    # Test audio au demarrage : sinon l'erreur ALSA n'apparait qu'au 1er appui,
    # noyee entre deux messages, et on ne sait pas quelles cartes existent.
    if ALSA_DEV:
        cartes = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
        if f"card {ALSA_DEV.split(':')[1].split(',')[0]}" not in cartes.stdout:
            print(f"ATTENTION: {ALSA_DEV} n'existe pas. Cartes disponibles :")
            for ligne in cartes.stdout.splitlines():
                if ligne.startswith("card "):
                    print("   ", ligne)
            print("    -> corriger ALSA_DEV en tete de diffuse.py")

    stop_txt = f" + stop sur GPIO{STOP_PIN}" if STOP_PIN else ""
    print(f"Ecoute de {len(SOUNDS)} boutons{stop_txt}... CTRL+C pour arreter.")
    # Etat initial lu sur les broches, pas suppose a 1 : si un bouton est
    # maintenu (ou cable normalement ferme) au demarrage, supposer 1 creerait
    # une fausse transition ou en manquerait une.
    prev = {p: GPIO.input(p) for p in broches}
    last = {p: 0.0 for p in broches}  # par broche : un 2e appui rapide interrompt quand meme
    try:
        while True:
            cur = {p: GPIO.input(p) for p in broches}
            appuis = transitions(prev, cur)

            # Le bouton stop peut etre actif haut : dans ce cas c'est la
            # transition inverse (LOW -> HIGH) qui correspond a l'appui.
            if STOP_PIN and not STOP_ACTIF_BAS:
                appuis = [p for p in appuis if p != STOP_PIN]
                if prev[STOP_PIN] == 0 and cur[STOP_PIN] == 1:
                    appuis.append(STOP_PIN)

            # Le stop est traite en premier et hors du "un seul par scan" :
            # s'il est presse en meme temps qu'un bouton son, il doit gagner.
            if STOP_PIN in appuis and time.time() - last[STOP_PIN] >= DEBOUNCE:
                last[STOP_PIN] = time.time()
                print(f"GPIO{STOP_PIN} -> stop")
                stop()
            else:
                for pin in appuis:
                    if pin == STOP_PIN:
                        continue
                    if time.time() - last[pin] >= DEBOUNCE:
                        last[pin] = time.time()
                        play(pin)
                        break  # un seul son a la fois (collision : ordre du dict)
            prev = cur
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("Arret.")
    finally:
        stop()
        GPIO.cleanup()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        assert transitions({5: 1}, {5: 0}) == [5]  # appui -> declenche
        assert transitions({5: 0}, {5: 0}) == []  # maintenu -> pas de repetition
        assert transitions({5: 0}, {5: 1}) == []  # relache -> rien
        assert len(SOUNDS) == 10  # 10 boutons
        assert len(set(SOUNDS.values())) == 6  # T00-T05
        assert len([p for p, s in SOUNDS.items() if s == SHARED]) == 5  # boutons 5-9
        assert STOP_PIN not in SOUNDS  # le bouton stop ne joue aucun son
        stop()  # sans rien en cours : ne doit pas lever
        print("selftest OK")
        sys.exit(0)
    main()
