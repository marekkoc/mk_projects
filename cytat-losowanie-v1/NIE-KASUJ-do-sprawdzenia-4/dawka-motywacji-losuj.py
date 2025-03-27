#!/usr/bin/env python
"""
C: 2020.12.15 / U: 2025.03.13
"""

import os
import sys
import random
from pathlib import Path

from motto import Motto
from file_paths import FilePaths
from motto_selector import MottoSelector

# 2021.10.19
hashseed = os.getenv('PYTHONHASHSEED')
if not hashseed:
    os.environ['PYTHONHASHSEED'] = '0'
    os.execv(sys.executable, [sys.executable] + sys.argv)
    
# Ścieżki do plików z motywacją
home_dir = Path.home()
pth =   home_dir / "programy" / "skrypty-git" / "dawka-motywacji" / "cytaty" / "dawka-motywacji"


motto_selector = MottoSelector(FilePaths(str(pth)))
motto = motto_selector.random_motto()
print(f"{motto.tekst}\n  ** {motto.autor} **")