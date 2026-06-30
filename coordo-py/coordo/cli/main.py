# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import signal
from pathlib import Path

import typer

from coordo.datapackage import DataPackage
from coordo.sql.builder import build_query
from .datapackage import add, remove, append, replace, delete
from ..map import Map

app = typer.Typer()
options = {}
static_dir = Path(__file__).parent / "static"


@app.callback()
def global_options(
    catalog: Path = typer.Option(Path("./catalog"), help="Root catalog folder"),
):
    options["catalog"] = catalog


@app.command()
def explore(package_path: Path):
    dp = DataPackage.from_path(package_path)
    conn, _ = dp.prepare_db()
    conn.execute("CALL start_ui();")
    signal.pause()


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
            map = coordo.createMap("#map", "/map/style.json");
          </script>
        </html>
        """

    @app.route("/map/<path:subpath>", methods=["GET", "POST"])
    def maps(subpath: str):
        return Map.from_file(
            config_file,
        ).handle_request(
            request.method,
            subpath,
            request.get_json(silent=True),
        )

    @app.route("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory(static_dir, filename)

    app.run(debug=True)
    

#################################################
# Loaders
# Load data from various sources into the datapackage.
##################################################

# Add a subcommand for each type of action with loaders
app.add_typer(add.app, name="add", help="Add a resource to the package")
app.add_typer(remove.app, name="remove", help="Remove a resource from the package")
app.add_typer(append.app, name="append", help="Append data of a resource in the package with new data")
app.add_typer(replace.app, name="replace", help="Replace data of a resource with new data")
app.add_typer(delete.app, name="delete", help="Delete the data of a resource")

#################################################
# Interaction with datapackage
##################################################

dp = typer.Typer()

@dp.command()
def query(
    package: Path,
    resource: str,
    select: str | None = typer.Option(None, "--select", "-s"),
    groupby: list[str] = typer.Option(None, "--group-by", "-g"),
):
    dp = DataPackage.from_path(package)
    columns = {}
    if select:
        for part in select.split(","):
            alias, expr = part.split(":")
            columns[alias] = expr
    conn, metadata = dp.prepare_db()
    query = build_query(metadata, resource, columns, None, groupby)
    conn.sql(str(query)).show()


app.add_typer(dp, name="dp")