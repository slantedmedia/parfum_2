# Préparer le raspberry

- Se connecter au raspberry avec Dataplicity

- `su pi`
- `treeosk`

## Raspbian Buster (EOL) — À FAIRE EN PREMIER

**À taper à la main sur le Pi, avant tout `git clone` / `git pull`.** Buster n'est plus
maintenu : ses dépôts ont été déplacés et les fichiers Release sont expirés, donc `apt`
refuse tout — y compris l'installation de `git`. Impossible de récupérer le dépôt tant que
ce n'est pas corrigé.

```bash
echo 'Acquire::Check-Valid-Until "false";' | sudo tee /etc/apt/apt.conf.d/10no-check-valid-until
sudo apt update
sudo apt install -y git
```

Si `apt update` échoue encore (`Repository ... has been moved`, `404 Not Found`), les URL
des dépôts sont mortes : basculer sur l'archive legacy.

```bash
cat /etc/apt/sources.list                    # verifier avant
sudo sed -i 's|raspbian.raspberrypi.org|legacy.raspbian.org|g; s|archive.raspbian.org|legacy.raspbian.org|g' /etc/apt/sources.list
sudo apt update
```

Le fichier doit contenir :

```
deb http://legacy.raspbian.org/raspbian/ buster main contrib non-free rpi
```

Penser aussi à `/etc/apt/sources.list.d/raspi.list` (dépôt Raspberry Pi Foundation, fichier
séparé) si des erreurs persistent.

Buster fournit **Python 3.7**, ce qui contraint plusieurs versions dans `install.sh`
(voir les commentaires du fichier) :
- `adafruit-circuitpython-typing==1.10.1` — à partir de 1.10.3 le paquet exige Python >=3.8
- `pip<25` — pip 24.0 est la dernière version compatible 3.7
- `python3-dev` + `build-essential` — `sysv-ipc` n'a pas de wheel ARM et doit être compilé

## Installation

(sur Buster, faire d'abord la section ci-dessus : sans ça `apt` et `git` ne marchent pas)

- `sudo apt update`

- `sudo apt install -y git`

- `git clone https://github.com/slantedmedia/parfum_2.git`

  Cloner **dans `/home/pi`** : tous les chemins des scripts sont en dur sur
  `/home/pi/parfum_2`.

- `cd parfum_2 && sh ./install.sh`

  Le script affiche `Finish - modules OK`, ou `ECHEC` avec le détail si pip a échoué.

- Vérifier : `env/bin/python -c "import RPi.GPIO, board, neopixel; print('ok')"`

  Attention à la casse : `RPi`, pas `RPI`. En cas d'échec, ne **jamais** faire
  `pip install board` ni `pip install neopixel` (paquets PyPI sans rapport qui masquent les
  vrais modules) — refaire `rm -rf env && sh ./install.sh`.

## Configurer le son

- `aplay -l` donne les numéros de carte (jack 3.5 mm = `Headphones`, l'autre = HDMI).

- Tester jusqu'à obtenir du son, en remplaçant le numéro de carte :

  `sudo ogg123 -q -d alsa -o dev:plughw:1,0 sounds/T00.wav`

  Utiliser `plughw:` et non `hw:` (conversion de format automatique).

- Reporter la valeur qui marche dans `ALSA_DEV`, en tête de `diffuse.py`.

- Si muet : `alsamixer -c 1` (`M` pour unmute), puis `sudo alsactl store` pour conserver le
  volume après reboot. Vérifier aussi `dtparam=audio=on` dans `/boot/config.txt`.

## Câblage des boutons

Chaque bouton relie sa broche GPIO à la masse (pull-up interne, appui = LOW).

| Bouton | GPIO | Son      | Bouton | GPIO | Son      |
|--------|------|----------|--------|------|----------|
| 0      | 5    | T00.wav  | 5      | 19   | T05.wav  |
| 1      | 6    | T01.wav  | 6      | 20   | T05.wav  |
| 2      | 12   | T02.wav  | 7      | 24   | T05.wav  |
| 3      | 13   | T03.wav  | 8      | 25   | T05.wav  |
| 4      | 16   | T04.wav  | 9      | 26   | T05.wav  |

## Tester

- `sudo /home/pi/parfum_2/env/bin/python /home/pi/parfum_2/diffuse.py`

  Affiche `Ecoute de 10 boutons...` puis `GPIO5 -> T00.wav` à chaque appui. `CTRL+C` pour
  arrêter.

## Configurer le démarrage automatique

- `crontab -e` et écrire, après les commentaires :

```
@reboot sudo /home/pi/parfum_2/env/bin/python /home/pi/parfum_2/diffuse.py >> /home/pi/diffuse.log 2>&1
```

- Vérifier après `sudo reboot` : `ps aux | grep diffuse` et `cat /home/pi/diffuse.log`

- Si le script ne démarre pas, `sudo` dans le crontab utilisateur peut demander un mot de
  passe : mettre la ligne dans `sudo crontab -e` et retirer le `sudo`.

**Ne pas** mettre `led_static.py` ni `start_up.sh` en autostart : ces scripts pilotent des
NeoPixel sur GPIO18, qui partage le matériel PWM du jack 3.5 mm et coupe le son.

### Mettre à jour le script

- Se placer dans le répertoire parfum_2:

- `cd /home/pi/parfum_2`

- `sh ./update.sh`

### Debugger le programme

- `cat /home/pi/diffuse.log`

- Ou lancer à la main : `sudo /home/pi/parfum_2/env/bin/python /home/pi/parfum_2/diffuse.py`

- Tester le câblage sans le son (toutes les broches à 1 au repos, 0 à l'appui) :

```bash
sudo env/bin/python -c "
import RPi.GPIO as G,time
P=[5,6,12,13,16,19,20,24,25,26]
G.setmode(G.BCM); G.setwarnings(False)
[G.setup(p,G.IN,pull_up_down=G.PUD_UP) for p in P]
while True:
    print('  '.join(f'{p}:{G.input(p)}' for p in P)); time.sleep(0.3)
"
```
