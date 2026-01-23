from . import to_maplibre

if __name__ == "__main__":
    import json

    with open("../config.json", "r") as file:
        config = json.load(file)

    print(to_maplibre(config))
