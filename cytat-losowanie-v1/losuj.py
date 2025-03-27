#!/home/marek/miniconda3/envs/py312/bin/python
"""
Losuje cytat z pliku np. dawka-motywacji.json

Created: 2025.03.04
Modified: 2025.03.15
Author: MK
"""


from mkquotes import FilePaths
from mkquotes import Odt2TxtConverter
from mkquotes import Txt2JsonConverter
from mkquotes import QuoteSelector

if __name__ == "__main__":
           
    def test1():
        names = ["dawka-motywacji", "52-notatki", "2007_Ruiz_Cztery-umowy"]
        for name in names:
            print("*"*100)
            print(f"Przetwarzanie pliku: {name}")

            file_paths = FilePaths(name)
            odt_converter = Odt2TxtConverter(file_paths)    
            odt_converter.odt_2_txt()        
            
            txt_json_converter = Txt2JsonConverter(file_paths)
            txt_json_converter.save_to_json()

            quote_selector = QuoteSelector(file_paths)
            print()
            print(f"Liczba autorów: {quote_selector.get_number_of_autors()}")
            print(f"Liczba cytatów: {quote_selector.get_number_of_quotes()}")
            print("-"*100)

            print(quote_selector.random_quote())
            print("-"*100)

            autor = quote_selector.random_autor()    
            cytaty = quote_selector.autor_quote_list[autor]
            print(f"{autor}:{quote_selector.autor_quote_count[autor]}")
            for k, cytat in enumerate(cytaty):
                print(f"   {k+1}. {cytat}")
            print("-"*100)
            print()

    def main():
        print()
        quote_selector = QuoteSelector(FilePaths("dawka-motywacji"))
        print(quote_selector.random_quote())
        print()

    main()  