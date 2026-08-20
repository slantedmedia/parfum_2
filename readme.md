# Répondeur téléphonique

Faux répondeur téléphonique sur Raspberry Pi : un vieux combiné dont les **9 touches
(1 à 9)** déclenchent chacune un message audio. Un **bouton stop** coupe le message en
cours.

- Chaque bouton a **son propre message** : bouton 1 → `bouton1.wav`, … bouton 9 →
  `bouton9.wav`, dans le dossier [sounds/](sounds/)
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

## 3. Les fichiers son

Neuf fichiers dans [sounds/](sounds/), un par bouton :

```
sounds/bouton1.wav   ...   sounds/bouton9.wav
```

Le nom **est** le mapping : pour changer le message du bouton 4, remplacer
`sounds/bouton4.wav` — rien à modifier dans le code.

Ces fichiers sont en **Ogg Vorbis malgré l'extension `.wav`** : c'est pour cela que le
script utilise `ogg123` et non `aplay`, qui les refuse. Un fichier ajouté doit donc être
encodé en Ogg :

```bash
ffmpeg -i mon_message.mp3 -c:a libvorbis sounds/bouton7.wav
```

Au démarrage, le script liste nommément les fichiers manquants
(`ATTENTION fichier manquant au demarrage: …`) avant de se mettre à écouter.

## 4. Configurer le son

```bash
aplay -l
```

Repérer la bonne carte — **la numérotation change d'un Pi à l'autre** :

- deux cartes → carte 0 = HDMI, carte 1 = `Headphones` (jack 3,5 mm)
- une seule carte → périphérique 0 = jack, 1 et 2 = HDMI

Tester jusqu'à obtenir du son :

```bash
sudo ogg123 -q -d alsa -o dev:plughw:1,0 sounds/bouton1.wav
sudo ogg123 -q -d alsa -o dev:plughw:0,0 sounds/bouton1.wav
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
dans le crontab (voir §7). Vérifier aussi `dtparam=audio=on` dans `/boot/config.txt` : si
l'audio interne est désactivé, la carte apparaît dans `aplay -l` mais refuse de s'ouvrir.

## 5. Câbler les boutons

Chaque bouton relie sa broche GPIO à la **masse** (pull-up interne, appui = LOW).

| Bouton | GPIO | Son |
|---|---|---|
| 1 | 5 | `bouton1.wav` |
| 2 | 6 | `bouton2.wav` |
| 3 | 12 | `bouton3.wav` |
| 4 | 13 | `bouton4.wav` |
| 5 | 16 | `bouton5.wav` |
| 6 | 19 | `bouton6.wav` |
| 7 | 20 | `bouton7.wav` |
| 8 | 26 | `bouton8.wav` |
| 9 | 21 | `bouton9.wav` |

**GPIO 24 et 25 sont libres** : c'étaient les boutons 8 et 9, déplacés. Pour rajouter un bouton, ajouter sa
ligne au dictionnaire `SOUNDS` en tête de [repondeur.py](repondeur.py) — tout le reste du
script s'adapte au nombre d'entrées.

### Bouton stop : GPIO 27

Le stop coupe le son en cours sans en lancer aucun. Deux constantes le règlent, en tête de
[repondeur.py](repondeur.py), et elles sont **indépendantes** :

| Constante | Valeurs | Rôle |
|---|---|---|
| `STOP_PULL` | `"up"` / `"down"` | la résistance interne activée sur la broche |
| `STOP_NIVEAU_APPUI` | `0` / `1` | la valeur lue **pendant** l'appui |

Selon le câblage, la résistance qui « voit » le bouton n'est pas forcément celle qu'on
déduirait du niveau d'appui — d'où deux réglages séparés, et non un seul booléen.

Câblages courants :

| Câblage | `STOP_PULL` | `STOP_NIVEAU_APPUI` |
|---|---|---|
| GPIO → bouton → GND | `"up"` | `0` |
| GPIO → bouton → 3,3 V | `"down"` | `1` |
| ce Pi (GND + 3,3 V) | `"up"` | `1` |

**Pour trancher, faire les 4 mesures** (les deux résistances × repos/appui) :

```bash
sudo env/bin/python -c "
import RPi.GPIO as G, time
G.setmode(G.BCM); G.setwarnings(False)
for nom, pull in (('up', G.PUD_UP), ('down', G.PUD_DOWN)):
    G.setup(27, G.IN, pull_up_down=pull); time.sleep(0.1)
    input('pull ' + nom + ' : RELACHER le bouton, puis Entree')
    repos = G.input(27)
    input('pull ' + nom + ' : MAINTENIR le bouton, puis Entree')
    print('  ->', nom, ': repos =', repos, ' appui =', G.input(27))
G.cleanup()
"
```

Lire le résultat ainsi :

- `STOP_PULL` = la résistance pour laquelle **repos et appui diffèrent**. Si les deux
  lignes donnent `repos = appui`, le bouton n'est pas câblé sur GPIO 27.
- `STOP_NIVEAU_APPUI` = la valeur `appui` lue sur cette ligne-là

Mettre `STOP_PIN = None` pour désactiver complètement le bouton stop.

## 6. Tester

```bash
sudo /home/pi/parfum_2/env/bin/python /home/pi/parfum_2/repondeur.py
```

Affiche `Ecoute de 9 boutons + stop sur GPIO27...`, puis `GPIO5 -> bouton1.wav` à chaque
appui. `CTRL+C` pour arrêter.

Les neuf broches doivent donner neuf noms de fichiers **différents** : deux boutons qui
affichent le même fichier signalent une erreur dans `SOUNDS`.

Si la carte indiquée dans `ALSA_DEV` n'existe pas, le script liste les cartes disponibles
dès le démarrage au lieu d'échouer à chaque appui.

## 7. Démarrage automatique

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

## 8. Mettre à jour

```bash
cd /home/pi/parfum_2
sh ./update.sh
```

(`git pull` puis redémarrage. Les fichiers son sont dans le dépôt, ils suivent.)

## 9. Dépannage

Vérifier la logique du script sans Pi ni carte son :

```bash
python repondeur.py --selftest      # doit afficher "selftest OK"
```

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
| `ATTENTION fichier manquant au demarrage` | le fichier nommé n'est pas dans `sounds/` | l'ajouter, encodé en Ogg (§3) |
| `ogg123: invalid option -- 'a'` | mauvaise syntaxe | `-d alsa -o dev:plughw:X,0` |
| `Cannot open plughw:X,0` | la carte X n'existe pas | `aplay -l` puis corriger `ALSA_DEV` |
| `Unknown PCM cards.pcm.front` | périphérique inexistant, repli ALSA | idem : corriger `ALSA_DEV` |
| Boutons OK mais aucun son | `ogg123` absent | `which ogg123`, sinon `sudo apt install -y vorbis-tools` |
| Le stop n'agit qu'au relâchement | `STOP_NIVEAU_APPUI` inversé | refaire les 4 mesures (§5) |
| Le stop n'agit jamais | mauvais `STOP_PULL` | idem : la bonne résistance est celle où repos ≠ appui |
| Un bouton ne répond pas | broche absente de `SOUNDS`, ou câblage | sonde ci-dessous, puis vérifier la table (§5) |
| Le volume retombe au reboot | `alsactl` / `alsa-restore` | régler le volume dans le crontab (§7) |

Tester le câblage sans le son — toutes les broches à `1` au repos, `0` à l'appui :

```bash
sudo env/bin/python -c "
import RPi.GPIO as G,time
P=[5,6,12,13,16,19,20,26,21,27]
G.setmode(G.BCM); G.setwarnings(False)
[G.setup(p,G.IN,pull_up_down=G.PUD_UP) for p in P]
while True:
    print('  '.join(f'{p}:{G.input(p)}' for p in P)); time.sleep(0.3)
"
```

(GPIO 27 est le stop : selon le câblage, il peut être à `0` au repos — voir §5.)
