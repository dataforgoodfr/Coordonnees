# Copyright COORDONNÉES 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import typer


def ensure_success(result: dict) -> dict:
    if not result.get("success", False):
        typer.echo(result.get("error", result.get("message", "Operation failed")), err=True)
        raise typer.Exit(code=1)
    return result