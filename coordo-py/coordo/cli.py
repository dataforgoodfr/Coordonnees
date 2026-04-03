import signal
from pathlib import Path

import typer
from dplib.models.schema.foreignKey import ForeignKey, ForeignKeyReference

from coordo import loaders
from coordo.datapackage import DataPackage
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
):
    dp = DataPackage.from_path(package)
    loaders.kobotoolbox.load(dp, xlsform, xlsdata)
    dp.save()


@load.command()
def file(
    path: Path,
    package: Path = typer.Option(".", help="Path to the package directory"),
):
    dp = DataPackage.from_path(package)
    try:
        loaders.file.load(dp, path)
    except ValueError as e:
        raise typer.BadParameter(
            f"{e} Add --overwrite if you wish to continue.", param_hint="path"
        )
    dp.save()


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
