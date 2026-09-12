#!/usr/bin/env bash
# Connecte la tablette Android puis lance parfum_2.py.
#
# 1. Tablette deja branchee en USB (ou deja appairee en Wi-Fi) -> on enchaine.
# 2. Sinon : scan du reseau local a la recherche du port ADB (5555),
#    "adb connect" sur les hotes trouves, et on recommence jusqu'a reussir.
#
# Ancien find-adb-device.sh, fusionne ici : un seul point d'entree pour cron.
#
# Prerequis cote tablette : "adb tcpip 5555" (une fois, en USB) et la cle du
# Pi autorisee ("Toujours autoriser") -- sinon l'appareil reste "unauthorized"
# et logcat ne renvoie rien.
# Prerequis cote Pi : sudo apt install -y nmap adb

set -uo pipefail  # pas de -e : le scan echoue souvent, c'est normal, on reessaie

# Tout doit tourner sous le MEME utilisateur qu'adb : root a son propre serveur
# adb, donc un "adb connect" en tant que pi serait invisible au python lance
# sous sudo. On passe root tout de suite, une bonne fois.
if [ "$(id -u)" -ne 0 ]; then
    exec sudo -- "$0" "$@"
fi

PORT="${ADB_PORT:-5555}"
INTERVAL="${RETRY_INTERVAL:-5}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-$DIR/env/bin/python}"

for outil in nmap adb; do
    command -v "$outil" >/dev/null 2>&1 || {
        echo "Erreur: '$outil' est requis mais introuvable (sudo apt install -y $outil)" >&2
        exit 1
    }
done

# Sous-reseau = celui de l'interface qui porte la route par defaut.
detect_subnet() {
    local iface cidr
    iface="$(ip -4 route show default 2>/dev/null | awk '{print $5; exit}')"
    [[ -n "${iface:-}" ]] && cidr="$(ip -4 -o addr show dev "$iface" 2>/dev/null | awk '{print $4; exit}')"
    [[ -z "${cidr:-}" ]] && cidr="$(ip -4 -o addr show scope global 2>/dev/null | awk '{print $4; exit}')"
    echo "${cidr:-}"
}

# Une tablette utilisable est-elle deja la (USB ou Wi-Fi deja appairee) ?
# "device" uniquement : "unauthorized" et "offline" ne servent a rien, logcat
# resterait muet et le script attendrait en silence.
deja_connecte() {
    adb devices 2>/dev/null | awk 'NR>1 && $2=="device" {trouve=1} END {exit !trouve}'
}

try_connect() {
    local ip="$1" out
    echo "-> Tentative ADB: ${ip}:${PORT}"
    out="$(adb connect "${ip}:${PORT}" 2>&1)"
    echo "$out"
    echo "$out" | grep -qiE 'connected to|already connected' || return 1
    case "$(adb -s "${ip}:${PORT}" get-state 2>/dev/null)" in
        device) return 0 ;;
        unauthorized)
            # On NE valide PAS : lancer le python ici donnerait un logcat vide.
            echo "   Appareil non autorise -- accepter 'Toujours autoriser' sur l'ecran de la tablette."
            return 1 ;;
        *) return 1 ;;
    esac
}

adb start-server >/dev/null 2>&1

essai=0
until deja_connecte; do
    essai=$((essai + 1))
    subnet="${TARGET_SUBNET:-$(detect_subnet)}"
    if [[ -z "$subnet" ]]; then
        echo "Sous-reseau introuvable (pas de reseau ?), nouvel essai dans ${INTERVAL}s"
        sleep "$INTERVAL"
        continue
    fi

    echo "=== Scan #${essai} de ${subnet} port ${PORT} ($(date '+%H:%M:%S')) ==="
    # -Pn : ne pas pinger d'abord (beaucoup de tablettes ignorent l'ICMP)
    # -n  : pas de resolution DNS
    mapfile -t hotes < <(nmap -Pn -n -p "$PORT" --open -oG - "$subnet" 2>/dev/null \
        | awk -v p="$PORT" '/Ports:/ && $0 ~ (" " p "/open/") {
              for (i = 1; i <= NF; i++) if ($i == "Host:") { print $(i + 1); break }
          }' | sort -u)

    if ((${#hotes[@]} == 0)); then
        echo "Aucun hote avec le port ${PORT} ouvert."
    else
        echo "Cibles: ${hotes[*]}"
        for ip in "${hotes[@]}"; do
            try_connect "$ip" && break
        done
    fi

    deja_connecte || { echo "Nouvel essai dans ${INTERVAL}s..."; sleep "$INTERVAL"; }
done

echo "Tablette connectee :"
adb devices -l

# exec : le python remplace ce shell, cron/systemd surveillent le bon process.
exec "$PYTHON" "$DIR/parfum_2.py"
