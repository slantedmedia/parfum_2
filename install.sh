sudo apt update && sudo apt install -y libopenblas-dev libatlas-base-dev gfortran python3-venv portaudio19-dev

# python3-dev + build-essential : sysv-ipc (dependance de Blinka) n'a pas de wheel ARM
# et doit etre compile -> sans les en-tetes Python on obtient
# "fatal error: Python.h: No such file or directory"
sudo apt install -y python3-dev build-essential

sudo apt install -y git adb

# ogg123 : lecture des .ogg (aplay ne sait pas decoder l'ogg)
sudo apt install -y vorbis-tools

python3 -m venv env

source ./env/bin/activate

# pip de Buster (18.x) est trop vieux pour lire les wheels recents.
# 24.0 = derniere version compatible Python 3.7.
/home/pi/parfum_2/env/bin/pip install --upgrade "pip<25"

/home/pi/parfum_2/env/bin/pip install RPi.GPIO

# NE PAS ajouter "pip install board" ni "pip install neopixel" : ce sont des paquets PyPI
# sans rapport qui masquent les vrais modules. board et neopixel viennent d'Adafruit-Blinka
# et adafruit-circuitpython-neopixel ci-dessous. C'est le bug qui a casse l'install avant.
# adafruit-circuitpython-typing : 1.10.1 et pas 1.11.2. A partir de 1.10.3 le paquet
# exige Python >=3.8, or Raspbian Buster fournit Python 3.7 -> "could not find a version
# that satisfies the requirement". 1.10.2 marche aussi mais est "yanked" sur PyPI
# (elle aurait du exiger 3.8) -> 1.10.1 est la derniere version propre pour 3.7.
# Blinka accepte n'importe quelle version de typing.
/home/pi/parfum_2/env/bin/pip install Adafruit-Blinka==8.50.0 adafruit-circuitpython-busdevice==5.2.10 adafruit-circuitpython-connectionmanager==3.1.2 adafruit-circuitpython-neopixel==6.3.13 adafruit-circuitpython-pixelbuf==2.0.6 adafruit-circuitpython-requests==4.1.8 adafruit-circuitpython-typing==1.10.1 Adafruit-PlatformDetect==3.76.1 Adafruit-PureIO==1.1.11


# Verification : sans ca le script affiche "Finish" meme quand pip a echoue.
if /home/pi/parfum_2/env/bin/python -c "import RPi.GPIO, board, neopixel" 2>/dev/null; then
    echo 'Finish - modules OK'
else
    echo 'ECHEC : les modules ne s importent pas. Detail :'
    /home/pi/parfum_2/env/bin/python -c "import RPi.GPIO, board, neopixel"
    exit 1
fi
