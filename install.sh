sudo apt update
sudo apt install libopenblas-dev
sudo apt install libatlas-base-dev
sudo apt install gfortran
sudo apt install python3-venv
sudo apt install portaudio19-dev
sudo apt install python3-venv

python3 -m venv env

source env/bin/activate

/home/pi/parfum_2/env/bin/pip install RPi.GPIO
/home/pi/parfum_2/env/bin/pip install board
/home/pi/parfum_2/env/bin/pip install neopixel
/home/pi/parfum_2/env/bin/pip install adafruit-blinka
/home/pi/parfum_2/env/bin/pip install adafruit-circuitpython-neopixel

echo 'Finish'