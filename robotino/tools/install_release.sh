#!/bin/sh
# Run on the Pi by deploy.ps1: point ~/robotino at this release. Deletes nothing.
# Usage: sh install_release.sh <commit> [branch]
set -eu
commit="$1"
branch="${2:-unknown}"
release="$HOME/robotino-releases/$commit"

if pgrep -f '[r]obotino_app.py' >/dev/null; then
    echo "The robot app is running: stop it with Ctrl+C, then deploy again."
    exit 3
fi
printf '%s (%s, deployed %s)\n' "$commit" "$branch" "$(date '+%Y-%m-%d %H:%M')" > "$release/VERSION"

# The first time, keep the old hand-copied folder under a new name.
if [ -e "$HOME/robotino" ] && [ ! -L "$HOME/robotino" ]; then
    backup="$HOME/robotino-before-releases"
    if [ -e "$backup" ]; then backup="$backup-$(date +%Y%m%d-%H%M%S)"; fi
    mv "$HOME/robotino" "$backup"
    echo "Kept the previous folder as $backup"
fi
ln -sfn "$release" "$HOME/robotino"

echo "Installed $commit ($branch): ~/robotino -> $release"
echo "Start:     cd ~/robotino && python3 robotino_app.py --hardware --servos"
echo "Terminal still inside the old folder? Run 'cd ~/robotino' again first."
echo "Go back:   ln -sfn ~/robotino-releases/<older commit> ~/robotino   (list: ls ~/robotino-releases)"
