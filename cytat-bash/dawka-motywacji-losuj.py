#!/usr/bin/env python
"""
Author: @marekkoc

Created: 2020.12.15 
Updated: 2025.03.20
"""

import os
import sys
import random
from pathlib import Path

#from mkenvs import EnvVars
from mkquotes import (
                    Quote,
                    QuoteSelector,
                    FilePaths,
                    JsonLoader
                    )

# 2025.03.20
quote_selector = QuoteSelector()
quote_selector.set_json_loader(JsonLoader(FilePaths("52-notatki", create="json")))
quote = quote_selector.random_quote()
print(f"{quote.tekst}\n  ** {quote.autor} **  ({quote.id})")

# 2025.03.19
# file_paths = FilePaths("dawka-motywacji")
# json_loader = JsonLoader(file_paths)
# quote_selector = QuoteSelector()
# quote_selector.set_json_loader(json_loader)
# quote = quote_selector.random_quote()
# print(f"{quote.tekst}\n  ** {quote.autor} **")

# 2025.03.17
#quote_selector = QuoteSelector(FilePaths("dawka-motywacji"))
#quote = quote_selector.random_quote()
#print(f"{quote.tekst}\n  ** {quote.autor} **")

# 2025.03.18    
#hashseed = os.getenv('PYTHONHASHSEED')
#if hashseed == '0':
#    # Usuń deterministyczne ustawienie
#    os.environ.pop('PYTHONHASHSEED', None)
#    os.execv(sys.executable, [sys.executable] + sys.argv)    

# 2021.10.19
#hashseed = os.getenv('PYTHONHASHSEED')
#if not hashseed:
#    os.environ['PYTHONHASHSEED'] = '0'
#    os.execv(sys.executable, [sys.executable] + sys.argv)
