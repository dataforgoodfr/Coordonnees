import os

import typer
from flask import request, send_from_directory

from . import loaders
from .config import MapConfig

app = typer.Typer()


@app.command()
def serve(config_file: str):
    from flask import Flask, jsonify

    app = Flask(__name__)
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    parser = MapConfig.from_file(config_file)

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
            map = coordo.createMap("#map", "style.json");
          </script>
        </html>
        """

    @app.route("/style.json")
    def style():
        return jsonify(parser.to_maplibre("/layers"))

    @app.route("/layers/<path:layer_id>", methods=["POST"])
    def layer_data(layer_id):
        return parser.get_data(layer_id, request.get_json())

    @app.route("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory(static_dir, filename)

    app.run(debug=True)


load = typer.Typer()

for name in loaders.__all__:
    module = getattr(loaders, name)

    cmd_name = name.replace("_", "-")
    load.command(name=cmd_name)(module.load)

app.add_typer(load, name="load")
