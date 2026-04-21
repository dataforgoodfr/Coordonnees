import shutil
from typer.testing import CliRunner
from coordo.cli import app 

runner = CliRunner()

def get_output_and_check_exitcode(result):
    print(result.stdout_bytes.decode())
    assert result.exit_code == 0

def test_add_package(inventory_package, inventory_inquiry, inventory_data, inventory_file):
    result1 = runner.invoke(app, ["load", "kobotoolbox", str(inventory_inquiry), str(inventory_data), "--package", inventory_package, "--action", "add"])
    get_output_and_check_exitcode(result1)
    result2 = runner.invoke(app, ["load", "file", str(inventory_file), "--package", inventory_package, "--action", "add"])
    get_output_and_check_exitcode(result2)
    result3 = runner.invoke(app, ["add-foreignkey", "ind.ess_arb", "file.ess_arb", "--package", inventory_package])
    get_output_and_check_exitcode(result3)
    print(f"Removing package '{inventory_package}'")
    shutil.rmtree(inventory_package)