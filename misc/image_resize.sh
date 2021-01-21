#!/bin/bash

minimumWidth=$1
minimumHeight=$1

f=$2

imageWidth=$(identify -format "%w" "$f") || exit 1
imageHeight=$(identify -format "%h" "$f") || exit 1

if [ "$imageWidth" -gt "$minimumWidth" ] || [ "$imageHeight" -gt "$minimumHeight" ]; then
	echo "Resizing image: $f"
  mogrify -resize ''"$minimumWidth"x"$minimumHeight"'' "$f" || exit 1
fi
