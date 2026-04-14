# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import signal
from pathlib import Path
from typing import Annotated

import typer
from dplib.models.schema.foreignKey import ForeignKey, ForeignKeyReference

from coordo.loaders import KoboToolboxLoader, FileLoader
from coordo.datapackage import DataPackage, ResourceExistsStrategy
from coordo.sql.builder import build_query

from .map import Map

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


load = typer.Typer()


@load.command()
def kobotoolbox(
    xlsform: Path,
    xlsdata: Path,
    package: Path = typer.Option(help="Path to the package directory"),
    strategy: Annotated[
        ResourceExistsStrategy,
        typer.Option(help="Strategy to use in case of already existing resource"),
    ] = ResourceExistsStrategy.raise_error,
):
    KoboToolboxLoader(package, xlsform, xlsdata, strategy).etl()


@load.command()
def file(
    path: Path,
    package: Path = typer.Option(".", help="Path to the package directory"),
    strategy: Annotated[
        ResourceExistsStrategy,
        typer.Option(help="Strategy to use in case of already existing resource"),
    ] = ResourceExistsStrategy.raise_error,
):
    FileLoader(package, path, strategy).etl()


app.add_typer(load, name="load")


@app.command()
def add_foreignkey(
    from_: str,
    to: str,
    package: Path = typer.Option(".", help="Path to the package directory"),
):
    dp = DataPackage.from_path(package)
    resource, field = from_.split(".")
    foreign_resource, foreign_field = to.split(".")
    dp.get_resource(
        resource,
    ).add_foreignkey(
        ForeignKey(
            fields=[field],
            reference=ForeignKeyReference(
                fields=[foreign_field],
                resource=None if resource == foreign_resource else foreign_resource,
            ),
        ),
    )
    dp.save()


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
