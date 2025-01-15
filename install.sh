sudo apt update
sudo apt install libopenblas-dev
sudo apt install libatlas-base-dev
sudo apt install gfortran
sudo apt install python3-venv
sudo apt install portaudio19-dev
sudo apt install python3-venv

python3 -m venv env

source env/bin/activate

pip install RPi.GPIO
pip install board
pip install neopixel
pip install adafruit-blinka
pip install adafruit-circuitpython-neopixel