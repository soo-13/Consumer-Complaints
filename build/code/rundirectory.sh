#!/bin/bash


#####################
### run build dir ###
#####################
python merging_ACS_dataset.py
python build_data.py
python explore.py

# copy the output to the folder synced to overleaf
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # current directory where this shell script is 
echo $SCRIPT_DIR

SRC_DIR="$(cd "$SCRIPT_DIR/../output" && pwd)"
DST_DIR="$(cd "$SCRIPT_DIR/../../../../Apps/Overleaf/Consumer-Complaints/build-output" && pwd)"
ANLS_DIR="$(cd "$SCRIPT_DIR/../../analysis/input" && pwd)"
echo $SRC_DIR
echo $DST_DIR

EXTENSIONS="pdf png jpg"

for ext in $EXTENSIONS; do
    cp "$SRC_DIR"/*.$ext "$DST_DIR"/
done

EXTENSIONS="csv xlsx json"

for ext in $EXTENSIONS; do
    cp "$SRC_DIR"/*.$ext "$ANLS_DIR"/
done
