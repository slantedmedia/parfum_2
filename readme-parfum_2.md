# Diffuseur de parfum — installation sur un Raspberry Pi

Borne de diffusion de parfum pilotée par une **tablette Android**. La tablette écrit une
ligne dans sa console à chaque appui sur un bouton de son interface ; le Raspberry lit
cette console via **adb** (USB ou Wi-Fi) et envoie une impulsion de 5 s sur le GPIO
correspondant, qui commande un diffuseur. Un bandeau de LEDs s'allume en blanc pendant
l'impulsion.

| Fichier | Rôle |
|---|---|
| [parfum_2.py](parfum_2.py) | écoute la console, pilote les GPIO et les LEDs |
| [start_up.sh](start_up.sh) | trouve la tablette sur le réseau, connecte adb, lance le script |
| [install.sh](install.sh) | installe les dépendances |

> Ce fichier ne concerne **que** le diffuseur de parfum. Le faux répondeur téléphonique
> (`repondeur.py`, dossier `sounds/`) est un autre montage, documenté dans
> [readme.md](readme.md).

---

## 1. Ce qu'il faut

| Élément | Détail |
|---|---|
| Raspberry Pi | Pi 4, Raspberry Pi OS 64-bit à jour |
| Tablette Android | avec l'appli kiosque Treeosk, **sur le même réseau Wi-Fi** que le Pi |
| Carte relais | une voie par diffuseur, sur les GPIO 4, 17, 22 et 24 |
| LEDs | bandeau NeoPixel (WS2812) de 100 pixels sur le GPIO 18 |

Le Pi et la tablette doivent être sur **le même sous-réseau** : le Pi scanne son propre
réseau local pour trouver la tablette. Un réseau invité qui isole les appareils entre eux
(*AP isolation*) empêche la connexion.

---

## 2. Préparer le Raspberry

1. **Graver la carte SD** avec Raspberry Pi Imager :
   - Modèle : **Raspberry Pi 4**
   - OS : **Raspberry Pi OS (64-bit)**, dernière version
   - Dans les réglages (⚙) : activer **SSH**, définir l'utilisateur et son mot de passe,
     renseigner le **Wi-Fi**

2. **Démarrer le Pi** et le mettre à jour :

   ```bash
   sudo apt update && sudo apt full-upgrade -y
   ```

3. *(optionnel, mais pratique)* **Accès à distance** par Raspberry Pi Connect :

   ```bash
   sudo apt install -y rpi-connect
   rpi-connect on
   rpi-connect signin
   ```

---

## 3. Installer le projet

Le chemin n'a pas d'importance : les scripts se repèrent tout seuls. Les exemples
utilisent `/home/pi/parfum_2`, adaptez si votre utilisateur n'est pas `pi`.

```bash
cd ~
git clone https://github.com/slantedmedia/parfum_2.git
cd parfum_2
sh install.sh
chmod +x start_up.sh      # au cas où le bit exécutable soit perdu
```

`install.sh` installe `git`, `adb`, `nmap`, `vorbis-tools`, crée l'environnement Python
`env/` et y installe `RPi.GPIO` et les bibliothèques Adafruit (NeoPixel).

Le script doit finir par :

```
Finish - modules OK
```

**Toute autre fin est un échec**, même si des lignes défilent avant. Les messages
`ECHEC : ...` indiquent quoi réinstaller. Ne passez pas à la suite tant que vous ne voyez
pas `Finish - modules OK`.

---

## 4. Câbler et valider le matériel

Faites cette étape **avant** de toucher à la tablette : elle ne demande ni réseau ni adb,
et elle élimine la moitié des causes de panne.

### Diffuseurs

| Ligne dans la console | GPIO (BCM) | Broche physique |
|---|---|---|
| `treeosk-btn-4` (ou `treeosk-btn-04`) | 4 | 7 |
| `treeosk-btn-17` | 17 | 11 |
| `treeosk-btn-22` | 22 | 15 |
| `treeosk-btn-24` | 24 | 18 |

**Le nombre dans le log est le numéro de GPIO**, pas le numéro du bouton. Pour ajouter un
diffuseur, ajoutez son GPIO dans `PINS` en tête de [parfum_2.py](parfum_2.py) :

```python
PINS = {4, 17, 22, 24}
```

Tout numéro absent de cette liste est ignoré, même s'il apparaît dans la console. C'est
volontaire : une ligne de log malformée ne doit pas pouvoir piloter n'importe quelle
broche.

### Sens de commande du relais

Réglage `ACTIF`, en tête de `parfum_2.py`. Il dépend de la carte relais et **il n'y a pas
de valeur universelle** :

| Carte | Réglage |
|---|---|
| commande positive (*HIGH level trigger*) | `ACTIF = 1` ← valeur actuelle |
| commande par la masse (*LOW level trigger*) | `ACTIF = 0` |

Au repos, la broche est maintenue au niveau inverse — jamais laissée flottante, sinon
elle dérive et peut déclencher le relais toute seule.

### Test d'une voie, sans tablette

```bash
cd /home/pi/parfum_2
sudo env/bin/python parfum_2.py --test 17
```

Le diffuseur doit fonctionner 5 s, puis s'arrêter. Sinon :

| Ce qu'on observe | Ce qu'il faut faire |
|---|---|
| rien ne se passe | inverser `ACTIF` (`0` ↔ `1`) et refaire le test |
| ça démarre et ne s'arrête plus | `ACTIF` est à l'envers : le niveau de repos déclenche le relais |
| toujours rien avec les deux valeurs | le problème est en aval : voir ci-dessous |

En aval du Pi, dans l'ordre : le cavalier d'alimentation de la carte relais (`JD-VCC`)
est-il en place, la **masse est-elle commune** entre le Pi et la carte, et le moteur
tourne-t-il si l'on ponte les contacts du relais à la main. Un multimètre sur la broche
pendant `--test` tranche en dix secondes : elle doit basculer de 0 V à 3,3 V (ou
l'inverse selon `ACTIF`) pendant exactement 5 s.

### LEDs

Bandeau NeoPixel de 100 pixels sur le **GPIO 18** (broche 12), alimenté à part en 5 V,
masse commune avec le Pi. Il s'allume en blanc pendant l'impulsion. Pour un bandeau plus
court ou plus long, changer `NUM_PIXELS`.

---

## 5. Appairer la tablette Android

À faire **une seule fois**, tablette branchée en USB sur le Pi. Toujours `sudo adb`, jamais
`adb` seul : root et l'utilisateur ont chacun leur propre serveur adb et ne voient pas les
mêmes appareils.

1. Sur la tablette : **Paramètres → À propos**, tapoter 7 fois sur *Numéro de build* pour
   débloquer les **Options pour les développeurs**, puis y activer **Débogage USB**.

2. Brancher la tablette au Pi en USB :

   ```bash
   sudo adb devices
   ```

   Un écran de confirmation apparaît sur la tablette : cocher **Toujours autoriser depuis
   cet ordinateur**, puis **Autoriser**. Résultat attendu :

   ```
   List of devices attached
   R9XN20ABCDE     device
   ```

   > `unauthorized` = autorisation non accordée (déverrouiller l'écran).
   > `offline` = câble ou port défectueux. Rien du tout = câble **de charge seule**
   > (très fréquent) ou débogage USB désactivé.

3. **Activer l'ADB en Wi-Fi** et relever l'adresse de la tablette :

   ```bash
   sudo adb tcpip 5555                              # "restarting in TCP mode port: 5555"
   sudo adb shell ip -4 addr show wlan0 | grep inet # son IP Wi-Fi
   sudo adb connect <cette_IP>:5555                 # "connected to ..."
   ```

4. Débrancher l'USB. Le Pi retrouvera la tablette tout seul aux démarrages suivants.

> **`adb tcpip 5555` ne survit pas au redémarrage de la tablette** sur la plupart des ROM.
> Après chaque reboot de la tablette, il faut rebrancher l'USB et refaire l'étape 3.
> **Pour une borne en exploitation, laissez la tablette branchée en USB** : `start_up.sh`
> la détecte directement et saute toute la phase de scan. C'est nettement plus fiable.

Sur la tablette, pensez aussi à **Options développeur → Rester activé** et à garder le
Wi-Fi actif en veille : Android coupe le Wi-Fi en veille profonde, et l'appareil disparaît
alors du réseau.

---

## 6. Lancer à la main

```bash
cd /home/pi/parfum_2
./start_up.sh
```

Déroulé attendu :

```
=== Scan #1 de 192.168.1.0/24 port 5555 (14:32:05) ===
Cibles: 192.168.1.42
-> Tentative ADB: 192.168.1.42:5555
connected to 192.168.1.42:5555
Tablette connectee :
...
Attente de la tablette Android...
Connecte. Ecoute des evenements... CTRL+C pour arreter.
```

Puis, à chaque appui sur la tablette :

```
treeosk-btn-17 -> impulsion sur GPIO17
```

`CTRL+C` pour arrêter. Le script refuse de démarrer si une autre instance tourne déjà
(`Une instance tourne deja`) — c'est voulu, voir §8.

---

## 7. Démarrage automatique

Une fois le test manuel concluant :

```bash
crontab -e
```

Ajouter (adapter le chemin) :

```
@reboot sudo /home/pi/parfum_2/start_up.sh >> /home/pi/parfum_2/boot.log 2>&1
```

Puis tester pour de bon — en tuant d'abord ce qui tourne, sinon le verrou bloquera
l'instance du démarrage :

```bash
sudo pkill -f parfum_2.py ; sudo pkill -f start_up.sh
sudo reboot
tail -f /home/pi/parfum_2/boot.log     # après reconnexion
```

`boot.log` grossit indéfiniment avec `>>` (une ligne de scan toutes les 5 s tant que la
tablette est absente). Mettre `>` au lieu de `>>` pour ne garder que le démarrage courant.

---

## 8. Les trois pièges à connaître

Ce sont les seuls qui reviennent vraiment.

**Deux instances en parallèle.** Symptômes combinés très reconnaissables : le moteur ne
s'arrête plus *et* les appuis ne sont plus détectés. Les deux scripts s'appellent
mutuellement `adb logcat -c` et se vident le tampon. Depuis l'ajout du verrou `flock` le
cas ne peut plus se produire, mais si vous voyez ces symptômes :

```bash
pgrep -af "parfum_2.py|start_up.sh"     # deux lignes ou plus = c'est ça
sudo pkill -f parfum_2.py ; sudo pkill -f start_up.sh
```

**Deux serveurs adb.** `adb` lancé en tant qu'utilisateur et `sudo adb` sont deux serveurs
distincts, avec chacun sa liste d'appareils. Un `adb connect` fait en `pi` est invisible au
script lancé en root. Toujours `sudo adb`. En cas de doute :

```bash
adb kill-server ; sudo adb kill-server ; sudo adb devices
```

**La tablette a changé d'IP.** Cause n°1 des « ça marchait hier » : bail DHCP renouvelé.
`start_up.sh` la retrouve tout seul en rescannant — laissez-lui un cycle complet. Fixer un
bail statique sur la box évite le problème une fois pour toutes.

---

## 9. Dépannage

| Symptôme | Cause probable | Vérification |
|---|---|---|
| `permission denied` au lancement | bit exécutable absent | `chmod +x start_up.sh`, ou `bash start_up.sh` |
| `nmap est requis mais introuvable` | apt a échoué pendant l'install | `sudo apt install -y nmap adb` |
| `Sous-reseau introuvable` | pas de route par défaut (Wi-Fi pas encore monté) | `ip -4 route show default` |
| `Aucun hote avec le port 5555 ouvert` en boucle | `adb tcpip 5555` perdu au reboot de la tablette, ou tablette en veille | rebrancher l'USB, refaire §5.3 |
| `failed to connect ... Connection refused` | rien n'écoute sur 5555 à cette IP (mauvaise machine, ou mode TCP perdu) | refaire §5.3 et relever l'IP depuis la tablette |
| `Appareil non autorise` | autorisation ADB non accordée | déverrouiller la tablette, « Toujours autoriser » |
| Connecté, mais aucun appui détecté | l'appli n'écrit pas le tag attendu | `sudo adb logcat \| grep treeosk-btn` |
| Un bouton ne fait rien, les autres oui | son GPIO n'est pas dans `PINS` | comparer le tag vu dans logcat et la table du §4 |
| Impulsion affichée, diffuseur inerte | `ACTIF` inversé, ou câblage | `--test`, voir §4 |
| `boot.log` reste vide | *(corrigé)* sortie Python bufferisée | le lanceur utilise `python -u` |
| Tout marche à la main, rien au boot | mauvais chemin, ou instance déjà lancée | `crontab -l`, puis `cat boot.log` |

**Voir ce que la tablette envoie**, indépendamment du script — arrêtez-le d'abord, sinon
les deux se disputent le tampon :

```bash
sudo pkill -f parfum_2.py
sudo adb logcat | grep treeosk-btn
```

Si rien ne s'affiche quand on appuie sur la tablette, le problème est côté tablette, pas
côté Raspberry.

**Vérifier la logique du script** sans matériel ni tablette (marche aussi sur un PC) :

```bash
env/bin/python parfum_2.py --selftest      # doit afficher "selftest OK"
```

---

## 10. Réglages

En tête de [parfum_2.py](parfum_2.py) :

| Réglage | Défaut | Effet |
|---|---|---|
| `PINS` | `{4, 17, 22, 24}` | GPIO autorisés (§4) |
| `PULSE` | `5` | durée de l'impulsion, en secondes |
| `ACTIF` | `1` | niveau appliqué pendant l'impulsion (§4) |
| `COOLDOWN` | `2` | délai mini entre deux impulsions d'une même broche |
| `NUM_PIXELS` | `100` | nombre de LEDs du bandeau |

Dans [start_up.sh](start_up.sh), par variables d'environnement :

| Variable | Défaut | Effet |
|---|---|---|
| `ADB_PORT` | `5555` | port ADB scanné |
| `RETRY_INTERVAL` | `5` | secondes entre deux scans |
| `TARGET_SUBNET` | détecté | force le sous-réseau, ex. `192.168.1.0/24` |
| `PYTHON` | `env/bin/python` | interpréteur utilisé |

---

## 11. Mettre à jour

```bash
cd /home/pi/parfum_2
sudo pkill -f parfum_2.py ; sudo pkill -f start_up.sh
git pull
sudo reboot
```
