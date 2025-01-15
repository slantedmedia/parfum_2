# Préparer le raspberry

- Se connecter au raspberry avec Dataplicity

- `su pi`
- `treeosk`

- `sudo apt-get install git`

- `git clone https://github.com/JulienJcbs/parfum_2.git`

- `cd parfum_2 && sh ./install.sh`

## Configurer le démarage automatique

- `crontab -e` Et ecrire dedans : `@reboot /bin/bash /home/pi/parfum_2/start_up.sh` après les commentaires

### Mettre à jour le script

Se placer dans le répertoire parfum_2:

- `cd home/pi/parfum_2`

- `sh ./update.sh`

### Debugger le programme

Se placer dans le répertoire parfum_2:

- `cd home/pi/parfum_2`

- `sh ./start_up.sh`