"""
Pakiet do zarządzania cytatami motywacyjnymi.

Zawiera narzędzia do konwersji plików z cytatami oraz losowego wybierania cytatów.

Created by: marekkoc 

Created: 2025.03.15
Modified: 2025.03.15
"""

from mkquotes import FilePaths, Odt2TxtConverter, Txt2JsonConverter, QuoteSelector

from . import losuj
from . import losuj_qt

__all__ = ['FilePaths', 'Odt2TxtConverter', 'Txt2JsonConverter', 'QuoteSelector', 'losuj', 'losuj_qt']  