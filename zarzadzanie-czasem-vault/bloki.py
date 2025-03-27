import json
import os
class Bloki:
    def __init__(self, bloki_json):
        self.bloki_json = bloki_json
        if not os.path.exists(bloki_json):
            print(f"Plik {bloki_json} nie istnieje")
    
    def load_bloki(self):
        with open(self.bloki_json, 'r', encoding='utf-8') as file:
            data = json.load(file)
            self.bloki = data["bloki"]
            self.version = data["version"]
        return self.bloki

    

if __name__ == "__main__":
    bloki = Bloki("bloki.json")
    b = bloki.load_bloki()
    print(bloki.__str__(1))