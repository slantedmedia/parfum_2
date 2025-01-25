sudo apt update && sudo apt install -y libopenblas-dev libatlas-base-dev gfortran python3-venv portaudio19-dev

python3 -m venv env

source ./env/bin/activate

/home/pi/parfum_2/env/bin/pip install RPi.GPIO
/home/pi/parfum_2/env/bin/pip install board
/home/pi/parfum_2/env/bin/pip install adafruit-blinka
/home/pi/parfum_2/env/bin/pip install adafruit-circuitpython-neopixel
/home/pi/parfum_2/env/bin/pip uninstall neopixel
/home/pi/parfum_2/env/bin/pip uninstall adafruit-circuitpython-neopixel
/home/pi/parfum_2/env/bin/pip install adafruit-circuitpython-neopixel

echo 'Finish'
