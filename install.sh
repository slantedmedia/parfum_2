# Repertoire du projet, deduit de l emplacement de ce script.
# Ne pas coder /home/pi/parfum_2 en dur : l utilisateur n est pas toujours "pi"
# (ex: /home/treeosk/parfum_2) et tout echouait alors silencieusement.
DIR=$(cd "$(dirname "$0")" && pwd)
VENV="$DIR/env"

sudo apt update && sudo apt install -y libopenblas-dev libatlas-base-dev gfortran python3-venv portaudio19-dev

# python3-dev + build-essential : sysv-ipc (dependance de Blinka) n'a pas de wheel ARM
# et doit etre compile -> sans les en-tetes Python on obtient
# "fatal error: Python.h: No such file or directory"
sudo apt install -y python3-dev build-essential

sudo apt install -y git adb

# ogg123 : lecture des .ogg (aplay ne sait pas decoder l'ogg)
sudo apt install -y vorbis-tools

python3 -m venv "$VENV"

# Arret immediat si le venv n a pas ete cree : sinon toutes les lignes suivantes
# echouent une par une et l erreur ne remonte qu a la toute fin.
# Cause habituelle : python3-venv absent (apt casse).
if [ ! -x "$VENV/bin/python" ]; then
    echo 'ECHEC : le venv n a pas ete cree (env/bin/python absent).'
    echo '        sudo apt install -y python3-venv puis relancer.'
    exit 1
fi

# Pas de "source ./env/bin/activate" : c est une bashism qui casse sous dash
# (sh ./install.sh) et c est inutile, tout ci-dessous utilise des chemins absolus.

# pip de Buster (18.x) est trop vieux pour lire les wheels recents.
# 24.0 = derniere version compatible Python 3.7.
"$VENV/bin/pip" install --upgrade "pip<25"

"$VENV/bin/pip" install RPi.GPIO

# NE PAS ajouter "pip install board" ni "pip install neopixel" : ce sont des paquets PyPI
# sans rapport qui masquent les vrais modules. board et neopixel viennent d'Adafruit-Blinka
# et adafruit-circuitpython-neopixel ci-dessous. C'est le bug qui a casse l'install avant.
# adafruit-circuitpython-typing : 1.10.1 et pas 1.11.2. A partir de 1.10.3 le paquet
# exige Python >=3.8, or Raspbian Buster fournit Python 3.7 -> "could not find a version
# that satisfies the requirement". 1.10.2 marche aussi mais est "yanked" sur PyPI
# (elle aurait du exiger 3.8) -> 1.10.1 est la derniere version propre pour 3.7.
# Blinka accepte n'importe quelle version de typing.
"$VENV/bin/pip" install Adafruit-Blinka==8.50.0 adafruit-circuitpython-busdevice==5.2.10 adafruit-circuitpython-connectionmanager==3.1.2 adafruit-circuitpython-neopixel==6.3.13 adafruit-circuitpython-pixelbuf==2.0.6 adafruit-circuitpython-requests==4.1.8 adafruit-circuitpython-typing==1.10.1 Adafruit-PlatformDetect==3.76.1 Adafruit-PureIO==1.1.11


# Verification : sans ca le script affiche "Finish" meme quand pip ou apt a echoue.
# On teste les deux moities : le module Python ET le lecteur audio.
# RPi.GPIO est le seul module externe importe par diffuse.py (board/neopixel
# servaient aux anciens scripts LED et ne sont plus utilises).
ERREUR=0

if ! "$VENV/bin/python" -c "import RPi.GPIO" 2>/dev/null; then
    echo 'ECHEC : RPi.GPIO ne s importe pas. Detail :'
    "$VENV/bin/python" -c "import RPi.GPIO"
    ERREUR=1
fi

# ogg123 vient d apt (vorbis-tools) : si apt est casse, il manque et le kiosque
# detecte les boutons sans jamais emettre de son.
if ! command -v ogg123 >/dev/null 2>&1; then
    echo 'ECHEC : ogg123 introuvable -> pas de son.'
    echo '        Verifier apt puis : sudo apt install -y vorbis-tools'
    ERREUR=1
fi

if [ "$ERREUR" -eq 0 ]; then
    echo 'Finish - modules OK'
else
    exit 1
fi
