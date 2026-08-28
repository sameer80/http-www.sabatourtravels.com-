#!/bin/bash
set -euo pipefail
export DISPLAY=:1

# Launch Chrome if not already on chat page
if ! pgrep -f "google-chrome.*localhost:3000" >/dev/null; then
  google-chrome --new-window "http://localhost:3000/" >/dev/null 2>&1 &
  sleep 4
fi

sleep 1
xdotool search --name "AI SEO Manager" windowactivate 2>/dev/null || xdotool search --class chrome windowactivate
sleep 1

# Login if on login page
xdotool key Tab Tab Return
sleep 2

# Navigate to chat
google-chrome "http://localhost:3000/dashboard/chat" >/dev/null 2>&1 || true
sleep 3
xdotool search --name "AI SEO Chat" windowactivate 2>/dev/null || xdotool search --class chrome windowactivate
sleep 2

# Click suggestion chip
xdotool mousemove 700 280 click 1
sleep 4

# Type custom message
xdotool mousemove 700 650 click 1
sleep 0.5
xdotool type --delay 20 "Show my top SEO opportunities"
xdotool key Return
sleep 4

# Overview page
google-chrome "http://localhost:3000/dashboard" >/dev/null 2>&1 || true
sleep 3

echo "GUI demo steps completed"
