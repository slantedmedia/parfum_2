#!/bin/bash

export DISPLAY=:0
export XAUTHORITY=/home/micromachine/.Xauthority

# Boucle jusqu'à ce que adb logcat -c réussisse
while true; do
    # Tente d'exécuter adb logcat -c
    adb logcat -c
    # Vérifie si la commande précédente a réussi (code de sortie 0)
    if [ $? -eq 0 ]; then
        echo "adb logcat -c exécuté avec succès"
        break  # Sort de la boucle si réussi
    else
        echo "Erreur dans l'exécution de adb logcat -c. Nouvelle tentative..."
        sleep 2  # Attendre 2 secondes avant de réessayer
    fi
done

# Après que adb logcat -c ait réussi, exécuter le script Python
sudo /home/micromachine/Desktop/sacs/rfid/myenv/bin/python /home/micromachine/Desktop/folder/parfum.py