#!/usr/bin/env python
"""
C: 2020.12.15 / U: 2025.02.04
"""
import random
from datetime import datetime
from pathlib import Path

import os
import sys

# 2021.10.19
hashseed = os.getenv('PYTHONHASHSEED')
if not hashseed:
    os.environ['PYTHONHASHSEED'] = '0'
    os.execv(sys.executable, [sys.executable] + sys.argv)
    
    

pth = Path("/home/marek/programy/skrypty-git/20201215_dawka_motywacji.txt")
pth2 = Path("/media/marek/data2T/Dropbox/priv/codzienne/dawka_motywacji.txt")

random.seed(None)
with open(pth, encoding='utf-8-sig') as file_in:
    #lines = [l for l in file_in.readlines() if len(l)>1]
    lines = [l.strip("\n") for l in file_in.readlines()]
    lines = [l for l in lines if len(l)>1]
    #print(lines[:2], len(lines))
    mottos = []

    for  i in range(0,len(lines),2):
        s = f'{lines[i].strip()}\n  ** {lines[i+1].strip()} **\n'
        mottos.append(s)
#        print(s)        
#         print()
print(random.choice(mottos))  
