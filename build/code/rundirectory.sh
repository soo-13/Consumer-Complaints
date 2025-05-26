#!/bin/bash


#####################
### run build dir ###
#####################
python build_data.py
python explore.py

# copy the output to the folder synced to overleaf
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # current directory where this shell script is 
echo $SCRIPT_DIR

SRC_DIR="$(cd "$SCRIPT_DIR/../output" && pwd)"
DST_DIR="$(cd "$SCRIPT_DIR/../../../../Apps/Overleaf/Consumer-Complaints/build-output" && pwd)"
echo $SRC_DIR
echo $DST_DIR

EXTENSIONS="pdf png jpg"

for ext in $EXTENSIONS; do
    cp "$SRC_DIR"/*.$ext "$DST_DIR"/
done
