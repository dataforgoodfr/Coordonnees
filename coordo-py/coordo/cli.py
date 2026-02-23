from pathlib import Path

import typer

from coordo import loaders
from coordo.datapackage import DataPackage

from .map import Map

app = typer.Typer()
options = {}
static_dir = Path(__file__).parent / "static"


@app.callback()
def global_options(
    catalog: Path = typer.Option(Path("./catalog"), help="Root catalog folder")
):
    options["catalog"] = catalog


@app.command()
def serve(config_file: str):
    from flask import Flask, request, send_from_directory

    app = Flask(__name__)

    @app.route("/")
    def home():
        return """
        <!DOCTYPE html>
        <html>
          <head>
            <title>Coordo</title>
            <link href="/static/coordo.css" rel="stylesheet" />
            <script src="/static/coordo.iife.js"></script>
          </head>
          <body style="margin: 0">
            <div id="map" style="height: 100dvh"></div>
          </body>
          <script>
            map = coordo.createMap("#map", "/maps/style.json");
          </script>
        </html>
        """

    map = Map.from_file(config_file)

    @app.route("/maps/<path:path>", methods=["GET", "POST"])
    def maps(path: str):
        return map.handle_request(
            request.method,
            path,
            request.get_json(silent=True),
        )

    @app.route("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory(static_dir, filename)

    app.run(debug=True)


load = typer.Typer()


@load.command()
def kobotoolbox(
    xlsform: Path,
    xlsdata: Path,
    package: Path = typer.Option(help="Path to the package directory"),
):
    if package.exists():
        assert package.is_dir(), f"{package} is not a directory"
    else:
        package.mkdir(parents=True)
    package = package / "datapackage.json"
    if package.exists():
        dp = DataPackage.from_path(package)
        ok = typer.confirm(f"A package already exists at {package}. Continue ?")
        if not ok:
            raise typer.Abort()
        print(f"Loading package from {package}")
    else:
        print(f"Creating new package at {package}")
        dp = DataPackage(name=package.name, basepath=package.parent)
    loaders.kobotoolbox.load(dp, xlsform, xlsdata)
    dp.save()


@load.command()
def file(
    path: Path,
    package: Path = typer.Option(help="Path to the package directory"),
    # encoding: str = typer.Option(help="Encoding for text files"),
):
    loaders.file.load(path)


app.add_typer(load, name="load")
