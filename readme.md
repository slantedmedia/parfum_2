# Répondeur téléphonique

Faux répondeur téléphonique sur Raspberry Pi : un vieux combiné dont les **10 touches
(0 à 9)** déclenchent chacune un message audio. Un **bouton stop** coupe le message en
cours.

- Boutons **0 à 4** : chacun son propre message (`T00.wav` … `T04.wav`)
- Boutons **5 à 9** : tous le même message (`T05.wav`)
- Un nouvel appui **interrompt** le message en cours et lance le nouveau
- Le bouton **stop** coupe le son sans rien lancer

Le script est [repondeur.py](repondeur.py). Tout le reste (`parfum.py`, `parfum_2.py`,
`leds.py`, `led_button.py`, `led_static.py`, `start_up.sh`) provient d'anciennes versions
du projet et **n'est plus utilisé**.

---

## 1. Préparer le Raspberry

Matériel : **Raspberry Pi 4**, avec la **dernière version de Raspberry Pi OS**.

1. **Graver la carte SD** avec Raspberry Pi Imager :
   - Modèle : **Raspberry Pi 4**
   - OS : **Raspberry Pi OS (64-bit)**, dernière version
   - Dans les réglages (⚙) : activer **SSH**, définir l'utilisateur `pi` et son mot de
     passe, renseigner le Wi-Fi

2. **Démarrer le Pi**, puis mettre à jour :

   ```bash
   sudo apt update && sudo apt full-upgrade -y
   ```

3. **Connecter le Pi à Raspberry Pi Connect** (accès à distance : shell et écran) :

   ```bash
   sudo apt install -y rpi-connect
   rpi-connect on
   rpi-connect signin
   ```

   La commande affiche un lien et un code de vérification. Ouvrir le lien, se connecter
   avec le compte **technical@mytreeosk.com**, valider le code, puis donner un nom au Pi.
   Il apparaît ensuite sur [connect.raspberrypi.com](https://connect.raspberrypi.com).

   Vérifier : `rpi-connect status`

## 2. Installer

```bash
cd /home/pi
git clone https://github.com/slantedmedia/parfum_2.git
cd parfum_2
sh ./install.sh
```

Le dossier peut être n'importe où (`/home/pi/parfum_2`, `/home/treeosk/parfum_2`, …) : les
scripts déduisent leur chemin tout seuls. Adapter les commandes ci-dessous en conséquence.

Utiliser **`sh ./install.sh`** et non `./install.sh` (le fichier n'est pas exécutable), et
**sans `sudo`** sur le script entier : il contient déjà les `sudo` nécessaires, et tout
lancer en root crée un venv appartenant à root.

Le script se termine par `Finish - modules OK`, ou par `ECHEC` avec le détail. Il vérifie
les deux moitiés : le module Python **et** le lecteur audio.

### Vérifier

```bash
env/bin/python -c "import RPi.GPIO; print('ok')"
which ogg123
```

Attention à la casse : **`RPi`**, pas `RPI`. En cas d'échec, ne **jamais** faire
`pip install board` ni `pip install neopixel` : ce sont des paquets PyPI sans rapport qui
masquent les vrais modules. Refaire `rm -rf env && sh ./install.sh`.

## 3. Configurer le son

```bash
aplay -l
```

Repérer la bonne carte — **la numérotation change d'un Pi à l'autre** :

- deux cartes → carte 0 = HDMI, carte 1 = `Headphones` (jack 3,5 mm)
- une seule carte → périphérique 0 = jack, 1 et 2 = HDMI

Tester jusqu'à obtenir du son :

```bash
sudo ogg123 -q -d alsa -o dev:plughw:1,0 sounds/T00.wav
sudo ogg123 -q -d alsa -o dev:plughw:0,0 sounds/T00.wav
```

Puis reporter la valeur qui marche dans `ALSA_DEV`, en tête de [repondeur.py](repondeur.py).

**Points de syntaxe** (sources d'erreurs vécues) :

- `-d alsa -o dev:plughw:X,0` — deux-points, pas `dev=`. L'option `-a` **n'existe pas**
  (`ogg123: invalid option -- 'a'`)
- `plughw:` et non `hw:` — `plughw` convertit le format automatiquement, `hw` exige le
  format exact et renvoie `no such device`
- `Unknown PCM cards.pcm.front` signifie que le périphérique demandé n'existe pas et
  qu'ALSA est retombé sur un défaut inexistant sur Pi → corriger `ALSA_DEV`

### Volume

```bash
amixer -c 1 scontrols          # nom exact du controle (PCM ? Headphone ?)
amixer -c 1 sset PCM 100%
alsamixer -c 1                 # M pour unmute, fleches pour monter
sudo alsactl store             # conserver apres reboot
```

Si le volume retombe à chaque redémarrage malgré `alsactl store`, le régler directement
dans le crontab (voir §6). Vérifier aussi `dtparam=audio=on` dans `/boot/config.txt` : si
l'audio interne est désactivé, la carte apparaît dans `aplay -l` mais refuse de s'ouvrir.

## 4. Câbler les boutons

Chaque bouton relie sa broche GPIO à la **masse** (pull-up interne, appui = LOW).

| Bouton | GPIO | Son | Bouton | GPIO | Son |
|---|---|---|---|---|---|
| 0 | 5 | T00.wav | 5 | 19 | T05.wav |
| 1 | 6 | T01.wav | 6 | 20 | T05.wav |
| 2 | 12 | T02.wav | 7 | 24 | T05.wav |
| 3 | 13 | T03.wav | 8 | 25 | T05.wav |
| 4 | 16 | T04.wav | 9 | 26 | T05.wav |

**Bouton stop : GPIO 27.** Sa polarité dépend du câblage, d'où la constante
`STOP_ACTIF_BAS` en tête de `repondeur.py` :

| Câblage | Repos | Appui | Réglage |
|---|---|---|---|
| GPIO → bouton → GND | 1 | 0 | `STOP_ACTIF_BAS = True` |
| GPIO → bouton → 3,3 V | 0 | 1 | `STOP_ACTIF_BAS = False` |

Pour trancher, mesurer la broche (si le son ne s'arrête qu'au relâchement, la valeur est
inversée) :

```bash
sudo env/bin/python -c "
import RPi.GPIO as G, time
G.setmode(G.BCM); G.setwarnings(False)
G.setup(27, G.IN, pull_up_down=G.PUD_UP)
while True:
    print(G.input(27), end=' ', flush=True); time.sleep(0.2)
"
```

## 5. Tester

```bash
sudo /home/pi/parfum_2/env/bin/python /home/pi/parfum_2/repondeur.py
```

Affiche `Ecoute de 10 boutons + stop sur GPIO27...`, puis `GPIO5 -> T00.wav` à chaque
appui. `CTRL+C` pour arrêter.

Si la carte indiquée dans `ALSA_DEV` n'existe pas, le script liste les cartes disponibles
dès le démarrage au lieu d'échouer à chaque appui.

## 6. Démarrage automatique

```bash
crontab -e
```

Écrire, après les commentaires (`:wq` pour enregistrer sous vim) :

```
@reboot sleep 15; /usr/bin/amixer -c 1 sset PCM 100%; /home/pi/parfum_2/env/bin/python /home/pi/parfum_2/repondeur.py >> /home/pi/repondeur.log 2>&1
```

- **chemins absolus obligatoires** : cron n'a quasiment pas de PATH
- **`sleep 15`** : au `@reboot`, cron démarre souvent avant que la carte son soit prête
- **`;` et non `&&`** : le script démarre même si le réglage du volume échoue
- si le script ne démarre pas, `sudo` dans un crontab utilisateur peut réclamer un mot de
  passe : mettre la ligne dans `sudo crontab -e` et retirer le `sudo`

Vérifier après `sudo reboot` :

```bash
ps aux | grep repondeur
cat /home/pi/repondeur.log
```

**Ne pas** mettre `led_static.py` ni `start_up.sh` en démarrage automatique : ces anciens
scripts pilotent des NeoPixel sur GPIO18, qui partage le matériel PWM du jack 3,5 mm et
**coupe le son**.

## 7. Mettre à jour

```bash
cd /home/pi/parfum_2
sh ./update.sh
```

(`git pull` puis redémarrage. Les fichiers son sont dans le dépôt, ils suivent.)

## 8. Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `Syntax error: end of file unexpected` | fins de ligne CRLF (édition sous Windows) | `.gitattributes` force le LF ; sinon `dos2unix install.sh` |
| `le venv n a pas ete cree` | `python3-venv` absent, ou projet hors de `/home/pi` | `sudo apt install -y python3-venv`, puis `rm -rf env && sh ./install.sh` |
| `pip: command not found` | pip n'est pas global | utiliser `env/bin/pip` |
| `No module named 'RPI'` | casse | c'est `RPi`, avec un i minuscule |
| `No module named _rpi_ws281x` | module NeoPixel manquant | sans importance : `repondeur.py` n'utilise que `RPi.GPIO` |
| `Python.h: No such file or directory` | `python3-dev` absent | `sudo apt install -y python3-dev build-essential` |
| `unable to locate vorbis-tools` | listes apt vides | `sudo apt update` |
| Erreurs apt en cascade (`unmet dependencies`, `Failed to fetch`, `could not find a version`) | image trop ancienne, dépôts expirés | regraver une image récente (§1) |
| `ogg123: invalid option -- 'a'` | mauvaise syntaxe | `-d alsa -o dev:plughw:X,0` |
| `Cannot open plughw:X,0` | la carte X n'existe pas | `aplay -l` puis corriger `ALSA_DEV` |
| `Unknown PCM cards.pcm.front` | périphérique inexistant, repli ALSA | idem : corriger `ALSA_DEV` |
| Boutons OK mais aucun son | `ogg123` absent | `which ogg123`, sinon `sudo apt install -y vorbis-tools` |
| Le stop n'agit qu'au relâchement | polarité inversée | basculer `STOP_ACTIF_BAS` |
| Le volume retombe au reboot | `alsactl` / `alsa-restore` | régler le volume dans le crontab (§6) |

Tester le câblage sans le son — toutes les broches à `1` au repos, `0` à l'appui :

```bash
sudo env/bin/python -c "
import RPi.GPIO as G,time
P=[5,6,12,13,16,19,20,24,25,26,27]
G.setmode(G.BCM); G.setwarnings(False)
[G.setup(p,G.IN,pull_up_down=G.PUD_UP) for p in P]
while True:
    print('  '.join(f'{p}:{G.input(p)}' for p in P)); time.sleep(0.3)
"
```
