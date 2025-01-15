sudo apt update
sudo apt install libopenblas-dev
sudo apt install libatlas-base-dev
sudo apt install gfortran
sudo apt install python3-venv
sudo apt install portaudio19-dev
sudo apt install python3-venv

python3 -m venv env

source env/bin/activate

sudo /home/pi/parfum_2/env/bin/python pip install RPi.GPIO
sudo /home/pi/parfum_2/env/bin/python pip install board
sudo /home/pi/parfum_2/env/bin/python pip install neopixel
sudo /home/pi/parfum_2/env/bin/python pip install adafruit-blinka
sudo /home/pi/parfum_2/env/bin/python pip install adafruit-circuitpython-neopixel