#!/bin/sh

python kindle.py
convert kindle-output.svg -background "#FFFFFF" -flatten -rotate 90 kindle-output.png
pngcrush -c 0 -ow kindle-output.png
cp kindle-output.png ~/.bsk/kindle-output.png
