#!/bin/bash

export DISPLAY=:0
export XAUTHORITY=/home/micromachine/.Xauthority

# Plus d'attente d'adb ici : parfum_2.py fait "adb wait-for-device" lui-meme
# et se reconnecte si la tablette est debranchee en cours de route.
sudo /home/pi/parfum_2/env/bin/python /home/pi/parfum_2/parfum_2.py
