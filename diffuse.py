import os
import subprocess
import sys
import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None  # machine de dev / --selftest

BASE = "/home/pi/parfum_2/sounds"
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

# ponytail: liste argv, pas shell=True et pas de sudo -- sinon terminate() tue le shell
# (ou sudo, qui ne transmet pas SIGTERM) et l'interruption du son ne marche pas.
# Le script tourne deja en root. Si ogg123 est muet mais paplay marche, changer cette ligne.
#
# ALSA_DEV : sortie audio forcee. Le defaut d'ALSA est casse ici
# ("Unknown PCM cards.pcm.front") -> on nomme la carte explicitement.
# D'apres "aplay -l" sur ce Pi : carte 0 = HDMI, carte 1 = Headphones (jack 3.5mm).
# Mettre "hw:0,0" pour sortir sur HDMI, ou None pour le defaut ALSA.
ALSA_DEV = "hw:1,0"  # jack 3.5mm

PLAYER = ["ogg123", "-q"] + (["-d", "alsa", "-o", f"dev:{ALSA_DEV}"] if ALSA_DEV else [])

# Pas de env= : ogg123 parle directement a ALSA en root. L'ancien DISPLAY /
# XDG_RUNTIME_DIR servait uniquement a PulseAudio sous sudo.

DEBOUNCE = 0.25

current = None


def transitions(prev, cur):
    """Broches passees de HIGH a LOW (appui). Pure -> testable."""
    return [p for p in cur if cur[p] == 0 and prev.get(p, 1) == 1]


def play(pin):
    global current
    path = SOUNDS[pin]
    if not os.path.exists(path):
        print(f"Fichier manquant: {path}")
        return
    if current and current.poll() is None:
        current.terminate()
        current.wait()  # recupere le process, evite les zombies
    print(f"GPIO{pin} -> {os.path.basename(path)}")
    current = subprocess.Popen(PLAYER + [path])


def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in SOUNDS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    for path in sorted(set(SOUNDS.values())):
        if not os.path.exists(path):
            print(f"ATTENTION fichier manquant au demarrage: {path}")

    print(f"Ecoute de {len(SOUNDS)} boutons... CTRL+C pour arreter.")
    prev = {p: 1 for p in SOUNDS}
    last = {p: 0.0 for p in SOUNDS}  # par broche : un 2e appui rapide interrompt quand meme
    try:
        while True:
            cur = {p: GPIO.input(p) for p in SOUNDS}
            for pin in transitions(prev, cur):
                if time.time() - last[pin] >= DEBOUNCE:
                    last[pin] = time.time()
                    play(pin)
                    break  # un seul son a la fois (collision dans le meme scan : ordre du dict)
            prev = cur
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("Arret.")
    finally:
        if current and current.poll() is None:
            current.terminate()
        GPIO.cleanup()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        assert transitions({5: 1}, {5: 0}) == [5]  # appui -> declenche
        assert transitions({5: 0}, {5: 0}) == []  # maintenu -> pas de repetition
        assert transitions({5: 0}, {5: 1}) == []  # relache -> rien
        assert len(SOUNDS) == 10  # 10 boutons
        assert len(set(SOUNDS.values())) == 6  # T00-T05
        assert len([p for p, s in SOUNDS.items() if s == SHARED]) == 5  # boutons 5-9
        print("selftest OK")
        sys.exit(0)
    main()
