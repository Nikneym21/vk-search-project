#!/bin/zsh
cd "$(dirname "$0")"
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 main.py >> log.txt 2>&1 
 