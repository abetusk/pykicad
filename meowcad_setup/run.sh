#!/bin/bash
#
# This will run all the necessary files to generate 
# footprint and component json menu and location json
# files.


egrep '^DEF ' ../library/*.lib | cut -f1,2 -d' ' | cut -f3- -d'/' | ped 's/.lib:DEF//' > base_lib.raw
egrep '^\$MODULE ' ../modules/*.mod | cut -f3- -d'/' | ped 's/\.mod:\$MODULE//' > base_mod.raw
./setup_base_modlib.py

rm -rf eeschema
pushd ..
./genlibjson.py
popd
mv ../eeschema .

rm -rf pcb
pushd ..
./genmodjson.py
popd
mv ../pcb .



