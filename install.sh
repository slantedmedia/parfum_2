sudo apt update && sudo apt install -y libopenblas-dev libatlas-base-dev gfortran python3-venv portaudio19-dev

sudo apt install -y git adb

# ogg123 : lecture des .ogg (aplay ne sait pas decoder l'ogg)
sudo apt install -y vorbis-tools

python3 -m venv env

source ./env/bin/activate

/home/pi/parfum_2/env/bin/pip install RPi.GPIO

# NE PAS ajouter "pip install board" ni "pip install neopixel" : ce sont des paquets PyPI
# sans rapport qui masquent les vrais modules. board et neopixel viennent d'Adafruit-Blinka
# et adafruit-circuitpython-neopixel ci-dessous. C'est le bug qui a casse l'install avant.
/home/pi/parfum_2/env/bin/pip install Adafruit-Blinka==8.50.0 adafruit-circuitpython-busdevice==5.2.10 adafruit-circuitpython-connectionmanager==3.1.2 adafruit-circuitpython-neopixel==6.3.13 adafruit-circuitpython-pixelbuf==2.0.6 adafruit-circuitpython-requests==4.1.8 adafruit-circuitpython-typing==1.11.2 Adafruit-PlatformDetect==3.76.1 Adafruit-PureIO==1.1.11


echo 'Finish'
