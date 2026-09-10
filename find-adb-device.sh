#!/usr/bin/env bash
# Scanne le réseau local pour le port ADB (5555), puis se connecte.
# Relance le scan jusqu'à succès.

set -euo pipefail

PORT="${ADB_PORT:-5555}"
INTERVAL="${RETRY_INTERVAL:-5}"
NMAP_OPTS=(-Pn -n -p "$PORT" --open)

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Erreur: '$1' est requis mais introuvable." >&2
    exit 1
  }
}

need nmap
need adb

detect_subnet() {
  local iface cidr
  iface="$(ip -4 route show default 2>/dev/null | awk '{print $5; exit}')"
  if [[ -n "${iface:-}" ]]; then
    cidr="$(ip -4 -o addr show dev "$iface" 2>/dev/null | awk '{print $4; exit}')"
  fi
  if [[ -z "${cidr:-}" ]]; then
    cidr="$(ip -4 -o addr show scope global 2>/dev/null | awk '{print $4; exit}')"
  fi
  if [[ -z "${cidr:-}" ]]; then
    echo "Erreur: impossible de détecter le sous-réseau local." >&2
    exit 1
  fi
  echo "$cidr"
}

find_hosts() {
  local subnet="$1"
  # Hosts avec le port ouvert (format nmap -oG)
  nmap "${NMAP_OPTS[@]}" -oG - "$subnet" 2>/dev/null \
    | awk -v p="$PORT" '
        /Status: Up/ { next }
        /Ports:/ {
          if ($0 ~ (" " p "/open/")) {
            for (i = 1; i <= NF; i++) {
              if ($i == "Host:") { print $(i + 1); break }
            }
          }
        }
      '
}

try_adb_connect() {
  local ip="$1"
  local out
  echo "→ Tentative ADB: ${ip}:${PORT}"
  out="$(adb connect "${ip}:${PORT}" 2>&1)" || true
  echo "$out"
  # Succès typique: "connected to ..." ou déjà connecté
  if echo "$out" | grep -qiE 'connected to|already connected'; then
    if adb -s "${ip}:${PORT}" get-state 2>/dev/null | grep -qx device; then
      return 0
    fi
    # Certains appareils passent par "unauthorized" puis "device"
    if adb -s "${ip}:${PORT}" get-state 2>/dev/null | grep -qx unauthorized; then
      echo "Appareil trouvé mais non autorisé — accepte la demande USB/ADB sur l'écran."
      return 0
    fi
  fi
  return 1
}

main() {
  local subnet hosts ip attempt=0

  subnet="${TARGET_SUBNET:-$(detect_subnet)}"
  echo "Sous-réseau: $subnet"
  echo "Port:        $PORT"
  echo "Intervalle:  ${INTERVAL}s"
  echo

  adb start-server >/dev/null 2>&1 || true

  while true; do
    attempt=$((attempt + 1))
    echo "=== Scan #${attempt} ($(date '+%H:%M:%S')) ==="

    mapfile -t hosts < <(find_hosts "$subnet" | sort -u)

    if ((${#hosts[@]} == 0)); then
      echo "Aucun hôte avec le port ${PORT} ouvert."
    else
      echo "Cibles: ${hosts[*]}"
      for ip in "${hosts[@]}"; do
        if try_adb_connect "$ip"; then
          echo
          echo "OK — connecté à ${ip}:${PORT}"
          adb devices -l
          exit 0
        fi
      done
      echo "Connexion ADB échouée pour les cibles trouvées."
    fi

    echo "Nouvel essai dans ${INTERVAL}s…"
    echo
    sleep "$INTERVAL"
  done
}

main "$@"
