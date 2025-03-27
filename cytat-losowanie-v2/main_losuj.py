#!/home/marek/miniconda3/envs/py312/bin/python
"""
Program do zarzadzania cytatami.

Created: 2025.03.18
Modified: 2025.03.18
Author: MK
"""
import sys

from PyQt5 import QtWidgets, Qt
from MainWindow import Ui_MainWindow


from mkquotes import FilePaths
from mkquotes import JsonLoader
from mkquotes import Odt2TxtConverter
from mkquotes import Txt2JsonConverter
from mkquotes import QuoteSelector


class MainWindow():
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)
        MainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(MainWindow)

        self._create_selector()
        self.ui.button_random.clicked.connect(self.losuj_cytat)

        MainWindow.show()
        sys.exit(app.exec_())

    def _create_selector(self):
        file_paths = FilePaths("dawka-motywacji", create="json")
        self.quote_selector = QuoteSelector()
        self.quote_selector.set_json_loader(JsonLoader(file_paths))
        

    def losuj_cytat(self):           
        cytat = self.quote_selector.random_quote()
        self.cytat_id = cytat.id
        self.ui.label_cytat.setText(f"{cytat.tekst} ({cytat.id})")
        self.ui.label_autor.setText(cytat.autor)



    



if __name__ == "__main__":
   

    #ui.button_random.clicked.connect(losuj_cytat)


    MainWindow()