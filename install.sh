sudo apt update && sudo apt install -y libopenblas-dev libatlas-base-dev gfortran python3-venv portaudio19-dev

python3 -m venv env

source ./env/bin/activate

/home/pi/parfum_2/env/bin/pip install RPi.GPIO
/home/pi/parfum_2/env/bin/pip install board
/home/pi/parfum_2/env/bin/pip install adafruit-blinka
/home/pi/parfum_2/env/bin/pip uninstall adafruit-circuitpython-neopixel
/home/pi/parfum_2/env/bin/pip install uninstall
/home/pi/parfum_2/env/bin/pip install Adafruit-Blinka==8.50.0 adafruit-circuitpython-busdevice==5.2.10 adafruit-circuitpython-connectionmanager==3.1.2 adafruit-circuitpython-neopixel==6.3.13 adafruit-circuitpython-pixelbuf==2.0.6 adafruit-circuitpython-requests==4.1.8 adafruit-circuitpython-typing==1.11.2 Adafruit-PlatformDetect==3.76.1 Adafruit-PureIO==1.1.11


echo 'Finish'
