"""Tests for literalizer_cli."""

import pytest
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


@pytest.mark.xfail(reason="TDD: implement JSON-to-Python via literalizer")
def test_literalize_json_to_python() -> None:
    """JSON input is converted to Python literal syntax."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[],  # Reads from stdin when input provided
        input='{"a": 1, "b": [2, 3]}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    # Expected: Python literal like "{'a': 1, 'b': [2, 3]}"
    assert "'a'" in result.output
    assert "1" in result.output
