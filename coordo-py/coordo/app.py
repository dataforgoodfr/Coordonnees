from pathlib import Path

from flask import Flask, render_template

from coordo.datapackage import DataPackage

app = Flask(__name__)

CATALOG_DIR = Path("../catalog")  # change this


@app.route("/")
def catalog():
    packages = [
        DataPackage.from_path(p / "datapackage.json")
        for p in CATALOG_DIR.iterdir()
        if p.is_dir()
    ]
    return render_template("catalog.html", packages=packages)


@app.route("/<path:path>")
def datapackage(path: str):
    package = DataPackage.from_path(CATALOG_DIR / path / "datapackage.json")
    return render_template("datapackage.html", package=package)


if __name__ == "__main__":
    app.run(debug=True)
