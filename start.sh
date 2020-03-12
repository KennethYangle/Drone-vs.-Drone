#!/bin/bash
python3 tello_vs_tello.py | tee -a ./log/`date +%Y%m%d_%H%M%S_debug.log`