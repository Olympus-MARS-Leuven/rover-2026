#!/bin/bash

set -u

PI_HOST="robotino@robotino-pi.local"
SIMULATION=0
SHUTDOWN=0
URL="http://127.0.0.1:8765"

usage() {
    echo "Usage: $0 [--simulation] [--shutdown] [--pi-host user@host]"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --simulation)
            SIMULATION=1
            ;;
        --shutdown)
            SHUTDOWN=1
            ;;
        --pi-host)
            if [ "$#" -lt 2 ]; then
                usage >&2
                exit 2
            fi
            PI_HOST="$2"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if [ "$SIMULATION" -eq 1 ] && [ "$SHUTDOWN" -eq 1 ]; then
    echo "--simulation and --shutdown cannot be used together." >&2
    usage >&2
    exit 2
fi

if [ "$SHUTDOWN" -eq 1 ]; then
    echo "Shutting down the robot's Pi. Type the Pi password if asked."
    ssh -t "$PI_HOST" "sudo shutdown -h now"
    code=$?
    if [ "$code" -eq 0 ]; then
        echo "Wait about 20 seconds until the green light on the Pi stops flashing, then switch the robot off."
    fi
    read -r -p "Press Return to close this window."
    exit "$code"
fi

if [ "$SIMULATION" -eq 1 ]; then
    app_flags=""
else
    app_flags="--hardware --servos"
fi

echo "Connecting to the robot. Type the Pi password when asked (nothing shows while typing)."
echo "KEEP THIS Terminal window open while you drive. Press Ctrl+C here to stop the robot app."
echo ""

(
    attempt=0
    while [ "$attempt" -lt 180 ]; do
        if curl --fail --silent --max-time 2 "$URL/" >/dev/null 2>&1; then
            open "$URL"
            exit 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
) &
opener_pid=$!
trap 'kill "$opener_pid" 2>/dev/null || true' EXIT

ssh -t -L 8765:127.0.0.1:8765 -o ExitOnForwardFailure=yes "$PI_HOST" \
    "cd ~/robotino && python3 robotino_app.py $app_flags"
code=$?
kill "$opener_pid" 2>/dev/null || true
wait "$opener_pid" 2>/dev/null || true
trap - EXIT

echo ""
if [ "$code" -eq 0 ] || [ "$code" -eq 130 ]; then
    echo "The robot app has stopped."
else
    echo "Could not start the robot (code $code). Common causes:"
    echo " - Hostname not found: the robot may be off or starting, or this Mac is on another Wi-Fi."
    echo " - Address already in use: another Robotino tunnel or simulation is already open."
    echo " - Another Robotino hardware process: the app may already be running on the Pi."
    echo " - Permission denied: check the Pi username and password."
fi
read -r -p "Press Return to close this window."
exit "$code"
