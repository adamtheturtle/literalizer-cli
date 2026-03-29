"""Tests for literalizer_cli."""

import textwrap
from dataclasses import dataclass

import pytest
from click import ClickException
from click.testing import CliRunner
from literalizer._language import Language
from literalizer.languages import Java, Python, R, Rust
from pytest_regressions.file_regression import FileRegressionFixture

import literalizer_cli
from literalizer_cli import main


@dataclass(frozen=True, kw_only=True)
class ExceptionCase:
    """A real literalizer failure case and its expected CLI message."""

    input_format: str
    input_string: str
    language: Language
    error_on_coercion: bool
    expected: str


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
    expected = textwrap.dedent(
        text="""\
        {
            "a": 1,
            "b": (2, 3),
        }
    """
    )
    assert result.output == expected


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
    expected = textwrap.dedent(
        text="""\
        map[string]int{
            "a": 1,
        }
    """
    )
    assert result.output == expected


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
    expected = textwrap.dedent(
        text="""\
        {
            "a": 1,
            "b": (2, 3),
        }
    """
    )
    assert result.output == expected


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
    expected = textwrap.dedent(
        text="""\
        map[string]int{
            "a": 1,
        }
    """
    )
    assert result.output == expected


def test_custom_indent() -> None:
    """Custom indent string is used in output."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "python", "-f", "json", "--indent", "\t"],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = textwrap.dedent(
        text="""\
        {
        \t"a": 1,
        }
    """
    )
    assert result.output == expected


def test_pre_indent_level() -> None:
    """Pre-indent level adds indentation to each output line."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "python", "-f", "json", "--pre-indent-level", "1"],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = '    {\n        "a": 1,\n    }\n'
    assert result.output == expected


def test_no_include_delimiters() -> None:
    """Delimiters are omitted when --no-include-delimiters is used."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--no-include-delimiters",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = '"a": 1,\n'
    assert result.output == expected


def test_variable_name() -> None:
    """Variable name is included in output when specified."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--variable-name",
            "data",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = textwrap.dedent(
        text="""\
        data = {
            "a": 1,
        }
    """
    )
    assert result.output == expected


def test_no_new_variable() -> None:
    """Existing variable assignment when --no-new-variable is used."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "go",
            "-f",
            "json",
            "--variable-name",
            "data",
            "--no-new-variable",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = textwrap.dedent(
        text="""\
        data = map[string]int{
            "a": 1,
        }
    """
    )
    assert result.output == expected


def test_error_on_coercion() -> None:
    """--error-on-coercion raises error for heterogeneous types."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "rust",
            "-f",
            "json",
            "--error-on-coercion",
        ],
        input='[1, "a"]\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    expected = (
        "Error: Collection contains heterogeneous scalar types "
        "that would be coerced to strings\n"
    )
    assert result.output == expected


def test_invalid_json_is_shown_cleanly() -> None:
    """JSON parse failures are shown as CLI errors."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--language", "python", "--input-format", "json"],
        input='{"a": }\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    expected = "Error: Invalid JSON: Expecting value at line 1 column 7\n"
    assert result.output == expected


def test_invalid_yaml_is_shown_cleanly() -> None:
    """YAML parse failures are shown as CLI errors."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--language", "python", "--input-format", "yaml"],
        input="a: [1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    expected = (
        "Error: Invalid YAML: while parsing a flow sequence\n"
        '  in "<unicode string>", line 1, column 4:\n'
        "    a: [1\n"
        "       ^ (line: 1)\n"
        "expected ',' or ']', but got '<stream end>'\n"
        '  in "<unicode string>", line 2, column 1:\n'
        "    \n"
        "    ^ (line: 2)\n"
    )
    assert result.output == expected


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        ExceptionCase(
            input_format="json",
            input_string='{"": 1}\n',
            language=R(empty_dict_key=R.empty_dict_keys.ERROR),
            error_on_coercion=False,
            expected=(
                "R does not support empty-string dict keys. "
                "Use empty_dict_key=R.EmptyDictKey.POSITIONAL to emit them "
                "as unnamed list elements instead."
            ),
        ),
        ExceptionCase(
            input_format="json",
            input_string='[1, "a"]\n',
            language=Rust(sequence_format=Rust.sequence_formats.VEC),
            error_on_coercion=True,
            expected=(
                "Collection contains heterogeneous scalar types "
                "that would be coerced to strings"
            ),
        ),
        ExceptionCase(
            input_format="json",
            input_string="[null]\n",
            language=Java(sequence_format=Java.sequence_formats.LIST),
            error_on_coercion=False,
            expected=(
                "Java's List.of() does not accept null elements. "
                "Use sequence_format=ARRAY instead."
            ),
        ),
        ExceptionCase(
            input_format="json",
            input_string='{"a": }\n',
            language=Python(),
            error_on_coercion=False,
            expected="Invalid JSON: Expecting value at line 1 column 7",
        ),
        ExceptionCase(
            input_format="yaml",
            input_string="a: [1\n",
            language=Python(),
            error_on_coercion=False,
            expected=(
                "Invalid YAML: while parsing a flow sequence\n"
                '  in "<unicode string>", line 1, column 4:\n'
                "    a: [1\n"
                "       ^ (line: 1)\n"
                "expected ',' or ']', but got '<stream end>'\n"
                '  in "<unicode string>", line 2, column 1:\n'
                "    \n"
                "    ^ (line: 2)"
            ),
        ),
    ],
    ids=(
        "empty_dict_key",
        "heterogeneous_coercion",
        "null_in_collection",
        "json_parse",
        "yaml_parse",
    ),
)
def test_literalizer_exceptions_are_wrapped_as_click_exceptions(
    case: ExceptionCase,
) -> None:
    """Real literalizer exceptions are surfaced as Click exceptions."""
    with pytest.raises(expected_exception=ClickException) as exc_info:
        literalizer_cli.literalize_input(
            input_string=case.input_string,
            language=case.language,
            input_format=case.input_format,
            pre_indent_level=0,
            include_delimiters=True,
            variable_name=None,
            new_variable=True,
            error_on_coercion=case.error_on_coercion,
        )

    assert exc_info.value.message == case.expected


def test_sequence_format() -> None:
    """--sequence-format changes the sequence representation."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--sequence-format",
            "list",
        ],
        input="[1, 2, 3]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = textwrap.dedent(
        text="""\
        [
            1,
            2,
            3,
        ]
    """
    )
    assert result.output == expected


def test_set_format() -> None:
    """--set-format changes the set representation."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "yaml",
            "--set-format",
            "frozenset",
        ],
        input="!!set\n  a:\n  b:\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = textwrap.dedent(
        text="""\
        frozenset({
            "a",
            "b",
        })
    """
    )
    assert result.output == expected


def test_empty_dict_key_via_cli() -> None:
    """--empty-dict-key changes empty dict key handling."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "r",
            "-f",
            "json",
            "--empty-dict-key",
            "positional",
        ],
        input='{"": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0


def test_language_option_unsupported_for_language() -> None:
    """Error when a language option is not supported for the language."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--default-dict-key-type",
            "str",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code != 0
    expected = (
        "Usage: literalize [OPTIONS]\n"
        "Try 'literalize --help' for help.\n"
        "\n"
        "Error: --default-dict-key-type is not supported "
        "for language 'python'.\n"
    )
    assert result.output == expected


def test_language_option_invalid_value() -> None:
    """Error when a language option value is not valid."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--sequence-format",
            "invalid",
        ],
        input="[1]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code != 0
    expected = (
        "Usage: literalize [OPTIONS]\n"
        "Try 'literalize --help' for help.\n"
        "\n"
        "Error: Invalid value 'invalid' for "
        "--sequence-format. Valid choices: list, tuple.\n"
    )
    assert result.output == expected


def test_include_preamble() -> None:
    """--include-preamble outputs language preamble before the code."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "go",
            "-f",
            "json",
            "--variable-name",
            "data",
            "--include-preamble",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = textwrap.dedent(
        text="""\
        package main
        data := map[string]int{
            "a": 1,
        }
    """
    )
    assert result.output == expected


def test_sequence_format_case_insensitive() -> None:
    """--sequence-format accepts values case-insensitively."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--sequence-format",
            "LIST",
        ],
        input="[1, 2]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = textwrap.dedent(
        text="""\
        [
            1,
            2,
        ]
    """
    )
    assert result.output == expected


def test_line_ending() -> None:
    """--line-ending changes the line ending style."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "javascript",
            "-f",
            "json",
            "--variable-name",
            "data",
            "--line-ending",
            "none",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    # With line_ending=none, JavaScript should omit the trailing semicolon.
    assert ";" not in result.output


def test_default_dict_key_type() -> None:
    """--default-dict-key-type overrides the default dict key type."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "go",
            "-f",
            "json",
            "--default-dict-key-type",
            "int",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert "map[int]" in result.output


def test_default_dict_value_type() -> None:
    """--default-dict-value-type overrides the default dict value type."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "go",
            "-f",
            "json",
            "--default-dict-value-type",
            "MyType",
        ],
        input='{"a": 1, "b": "x"}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert "map[string]MyType" in result.output


def test_default_sequence_element_type() -> None:
    """--default-sequence-element-type overrides sequence element type."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "go",
            "-f",
            "json",
            "--default-sequence-element-type",
            "MyType",
        ],
        input='[1, "a"]\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert "[]MyType" in result.output


def test_default_set_element_type() -> None:
    """--default-set-element-type overrides the default set element type."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "csharp",
            "-f",
            "yaml",
            "--default-set-element-type",
            "MyType",
        ],
        input="!!set\n  1:\n  a:\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert "HashSet<MyType>" in result.output


def test_default_type_unsupported_for_language() -> None:
    """Error when a default type option is not supported for the language."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--default-sequence-element-type",
            "int",
        ],
        input="[1]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code != 0
    expected = (
        "Usage: literalize [OPTIONS]\n"
        "Try 'literalize --help' for help.\n"
        "\n"
        "Error: --default-sequence-element-type is not supported "
        "for language 'python'.\n"
    )
    assert result.output == expected
