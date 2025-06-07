#!/usr/bin/env python
"""
C: 2020.12.15 / U: 2025.03.05
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
    
# Ścieżki do plików z motywacją
pth = Path("/home/marek/programy/skrypty-git/dawka-motywacji/cytaty/dawka-motywacji.txt")

# Wybierz ścieżkę, która istnieje
file_path = pth

if file_path is None:
    print("Błąd: Nie znaleziono pliku z motywacją.")
    sys.exit(1)

try:
    random.seed(None)
    with open(file_path, encoding='utf-8-sig') as file_in:
        content = file_in.read()
        
        # Podziel zawartość na bloki cytatów (każdy cytat + autor)
        # Każdy blok jest oddzielony co najmniej dwoma pustymi liniami
        blocks = content.split('\n\n\n')
        
        mottos = []
        for block in blocks:
            if block.strip():  # Pomijaj puste bloki
                lines = [line.strip() for line in block.split('\n') if line.strip()]
                if len(lines) >= 2:
                    quote = lines[0]
                    author = lines[1]
                    s = f'{quote}\n  ** {author} **\n'
                    mottos.append(s)
                
    if mottos:
        print(random.choice(mottos))
    else:
        print("Nie znaleziono żadnych motywacyjnych cytatów w pliku.")
        
except Exception as e:
    print(f"Wystąpił błąd: {e}")
    sys.exit(1)  
