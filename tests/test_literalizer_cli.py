"""Tests for literalizer_cli."""

from click.testing import CliRunner
from pytest_regressions.file_regression import FileRegressionFixture

from literalizer_cli import main


def test_help(file_regression: FileRegressionFixture) -> None:
    """Expected help text is shown.

    This help text is defined in files.
    To update these files, run ``pytest`` with the ``--regen-all`` flag.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--help"],
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    file_regression.check(contents=result.output)


def test_literalize_json_to_python() -> None:
    """JSON input is converted to Python literal syntax."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--language", "python", "--input-format", "json"],
        input='{"a": 1, "b": [2, 3]}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert result.output == '{\n    "a": 1,\n    "b": (2, 3),\n}\n'


def test_literalize_json_to_go() -> None:
    """JSON input is converted to Go literal syntax."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "go", "-f", "json"],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert result.output == 'map[string]int{\n    "a": 1,\n}\n'


def test_literalize_yaml_to_python() -> None:
    """YAML input is converted to Python literal syntax."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--language", "python", "--input-format", "yaml"],
        input="a: 1\nb:\n  - 2\n  - 3\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert result.output == '{\n    "a": 1,\n    "b": (2, 3),\n}\n'


def test_literalize_yaml_short_flag() -> None:
    """YAML input works with the short -f flag."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "go", "-f", "yaml"],
        input="a: 1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert result.output == 'map[string]int{\n    "a": 1,\n}\n'
