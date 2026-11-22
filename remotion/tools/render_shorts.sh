#!/bin/bash
# Rendert alle Remotion-Videos als YouTube Shorts nach ../shorts/ (mit Lautstärke-Angleichung)
set -e
cd "$(dirname "$0")/.."
CH=${CHROME:-/opt/pw-browsers/chromium-1243/chrome-linux64/chrome}
declare -A OUT=( ["homework-excuse-en"]="homework-excuse-en" ["homework-excuse"]="hausaufgaben-ausrede-de" ["classroom-comedy"]="der-schlaue-schueler" ["surprise-test"]="surprise-test-scene1" ["homework-excuse-miss-en"]="homework-excuse-miss-en" ["homework-excuse-miss-de"]="hausaufgaben-ausrede-miss-de" )
IDS=${@:-homework-excuse-en homework-excuse classroom-comedy surprise-test homework-excuse-miss-en homework-excuse-miss-de}
for id in $IDS; do
  npx remotion render $id out/raw_$id.mp4 --browser-executable=$CH --chrome-mode=chrome-for-testing
  ffmpeg -y -loglevel error -i out/raw_$id.mp4 -af "loudnorm=I=-14:TP=-1.0:LRA=9" -c:v copy -c:a aac -b:a 192k -ar 48000 -movflags +faststart ../shorts/${OUT[$id]}.mp4
  rm -f out/raw_$id.mp4
  echo "FERTIG $id"
done
