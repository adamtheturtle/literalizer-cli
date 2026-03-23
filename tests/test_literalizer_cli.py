"""Tests for literalizer_cli."""

from click.testing import CliRunner

from literalizer_cli import main


def test_help() -> None:
    """Help text is shown."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--help"],
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert "literalize" in result.output
    assert "Convert data structures" in result.output


def test_literalize_json_to_python() -> None:
    """JSON input is converted to Python literal syntax."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--language", "python"],
        input='{"a": 1, "b": [2, 3]}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert "1" in result.output


def test_literalize_json_to_go() -> None:
    """JSON input is converted to Go literal syntax."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "go"],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert "1" in result.output


def test_language_required() -> None:
    """CLI errors when --language is not provided."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[],
        input='{"a": 1}\n',
    )
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output
