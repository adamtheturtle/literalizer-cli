"""Tests for literalizer_cli."""

import textwrap
from dataclasses import dataclass
from typing import Any

import pytest
from click import ClickException
from click.testing import CliRunner
from literalizer import ExistingVariable, InputFormat, NewVariable
from literalizer.languages import Java, Python, R, Rust
from pytest_regressions.file_regression import FileRegressionFixture

import literalizer_cli
from literalizer_cli import main


@dataclass(frozen=True, kw_only=True)
class ExceptionCase:
    """A real literalizer failure case and its expected CLI message."""

    input_format: InputFormat
    input_string: str
    language: Any
    expected: str
    variable_form: NewVariable | ExistingVariable | None = None


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


def test_ref_case_emits_bare_identifiers() -> None:
    """``--ref-case`` re-cases ``$ref`` markers to bare identifiers."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "--language",
            "python",
            "--input-format",
            "json",
            "--ref-case",
            "snake",
        ],
        input='{"a": {"$ref": "userId"}}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected = textwrap.dedent(
        text="""\
        {
            "a": user_id,
        }
    """
    )
    assert result.output == expected


def test_ref_case_unsupported_for_language() -> None:
    """An unsupported ref-case for the language exits with a clean error."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "--language",
            "python",
            "--input-format",
            "json",
            "--ref-case",
            "camel",
        ],
        input='{"a": {"$ref": "userId"}}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert (
        result.output
        == "Error: Python does not support identifier case 'CAMEL'\n"
    )


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


def test_heterogeneous_collection_error() -> None:
    """Heterogeneous scalar collections surface as CLI errors."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "rust",
            "-f",
            "json",
        ],
        input='[1, "a"]\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    expected = (
        "Error: Collection contains heterogeneous scalar types that "
        "cannot be represented in the target language "
        "(found types: int, str)\n"
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
        '  in "<unicode string>", line 1, column 4\n'
        "did not find expected ',' or ']'\n"
        '  in "<unicode string>", line 2, column 1\n'
    )
    assert result.output == expected


@pytest.mark.parametrize(
    argnames="case",
    argvalues=[
        ExceptionCase(
            input_format=InputFormat.JSON,
            input_string='{"": 1}\n',
            language=R(empty_dict_key=R.empty_dict_keys.ERROR),
            expected=(
                'R does not support the dict key "". '
                "Use empty_dict_key=R.EmptyDictKey.POSITIONAL to emit them "
                "as unnamed list elements instead."
            ),
        ),
        ExceptionCase(
            input_format=InputFormat.JSON,
            input_string='[1, "a"]\n',
            language=Rust(sequence_format=Rust.sequence_formats.VEC),
            expected=(
                "Collection contains heterogeneous scalar types that "
                "cannot be represented in the target language "
                "(found types: int, str)"
            ),
        ),
        ExceptionCase(
            input_format=InputFormat.JSON,
            input_string="[null]\n",
            language=Java(sequence_format=Java.sequence_formats.LIST),
            expected=(
                "Java's List.of() does not accept null elements"
                " (got 1 items, including null)."
                " Use sequence_format=ARRAY instead."
            ),
        ),
        ExceptionCase(
            input_format=InputFormat.JSON,
            input_string='{"a": }\n',
            language=Python(),
            expected="Invalid JSON: Expecting value at line 1 column 7",
        ),
        ExceptionCase(
            input_format=InputFormat.YAML,
            input_string="a: [1\n",
            language=Python(),
            expected=(
                "Invalid YAML: while parsing a flow sequence\n"
                '  in "<unicode string>", line 1, column 4\n'
                "did not find expected ',' or ']'\n"
                '  in "<unicode string>", line 2, column 1'
            ),
        ),
    ],
    ids=(
        "empty_dict_key",
        "heterogeneous_collection",
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
            variable_form=case.variable_form,
            wrap_in_file=False,
            ref_case=None,
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
            "ada",
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
        "for language 'ada'.\n"
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
            "ada",
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
        "for language 'ada'.\n"
    )
    assert result.output == expected


def test_literalize_json5_to_python() -> None:
    """JSON5 input is converted to Python literal syntax."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "python", "-f", "json5"],
        input="{a: 1, b: [2, 3]}\n",
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


def test_literalize_toml_to_python() -> None:
    """TOML input is converted to Python literal syntax."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "python", "-f", "toml"],
        input="a = 1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = textwrap.dedent(
        text="""\
        {
            "a": 1,
        }
    """
    )
    assert result.output == expected


def test_invalid_json5_is_shown_cleanly() -> None:
    """JSON5 parse failures are shown as CLI errors."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--language", "python", "--input-format", "json5"],
        input="{a: }\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_invalid_toml_is_shown_cleanly() -> None:
    """TOML parse failures are shown as CLI errors."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--language", "python", "--input-format", "toml"],
        input="= bad\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_trailing_comma_option() -> None:
    """--trailing-comma controls trailing comma behavior."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--trailing-comma",
            "no",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = textwrap.dedent(
        text="""\
        {
            "a": 1
        }
    """
    )
    assert result.output == expected


def test_modifier_option_java() -> None:
    """--modifier adds declaration modifiers in supported languages."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "java",
            "-f",
            "json",
            "--variable-name",
            "DATA",
            "--modifier",
            "public",
            "--modifier",
            "static",
            "--modifier",
            "final",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, result.output
    expected = textwrap.dedent(
        text="""\
        public static final Map<String, Integer> DATA = Map.ofEntries(
            Map.entry("a", 1)
        );
    """
    )
    assert result.output == expected


def test_modifier_option_case_insensitive() -> None:
    """--modifier accepts values case-insensitively."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "csharp",
            "-f",
            "json",
            "--variable-name",
            "Data",
            "--modifier",
            "READONLY",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, result.output
    expected = textwrap.dedent(
        text="""\
        readonly Dictionary<string, int> Data = new Dictionary<string, int> {
            ["a"] = 1
        };
    """
    )
    assert result.output == expected


def test_modifier_unsupported_for_language() -> None:
    """Error when --modifier is used with a language without modifiers."""
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
            "--modifier",
            "final",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    expected = (
        "Usage: literalize [OPTIONS]\n"
        "Try 'literalize --help' for help.\n"
        "\n"
        "Error: --modifier is not supported for language 'python'.\n"
    )
    assert result.exit_code != 0
    assert result.output == expected


def test_modifier_invalid_value() -> None:
    """Error when --modifier is given a value the language does not support."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "java",
            "-f",
            "json",
            "--variable-name",
            "data",
            "--modifier",
            "readonly",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    expected = (
        "Usage: literalize [OPTIONS]\n"
        "Try 'literalize --help' for help.\n"
        "\n"
        "Error: Invalid value 'readonly' for --modifier. "
        "Valid choices: final, private, protected, public, static.\n"
    )
    assert result.exit_code != 0
    assert result.output == expected


def test_modifier_requires_variable_name() -> None:
    """--modifier without --variable-name is a usage error."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "java",
            "-f",
            "json",
            "--modifier",
            "final",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    expected = (
        "Usage: literalize [OPTIONS]\n"
        "Try 'literalize --help' for help.\n"
        "\n"
        "Error: --modifier requires --variable-name.\n"
    )
    assert result.exit_code != 0
    assert result.output == expected


def test_modifier_conflicts_with_no_new_variable() -> None:
    """--modifier with --no-new-variable is a usage error."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "java",
            "-f",
            "json",
            "--variable-name",
            "data",
            "--no-new-variable",
            "--modifier",
            "final",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    expected = (
        "Usage: literalize [OPTIONS]\n"
        "Try 'literalize --help' for help.\n"
        "\n"
        "Error: --modifier cannot be used with --no-new-variable.\n"
    )
    assert result.exit_code != 0
    assert result.output == expected


def test_declaration_style_option() -> None:
    """--declaration-style changes the variable declaration style."""
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
            "--declaration-style",
            "const",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert "const data" in result.output


def test_call_mode() -> None:
    """--mode call converts data to function call expressions."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-function",
            "create_user",
            "--call-params",
            "name,age",
        ],
        input='[["alice", 30], ["bob", 25]]\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    expected = (
        'create_user(name="alice", age=30)\ncreate_user(name="bob", age=25)\n'
    )
    assert result.output == expected


def test_call_mode_no_per_element() -> None:
    """--no-per-element passes the whole value as a single argument."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-function",
            "process",
            "--call-params",
            "data",
            "--no-per-element",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert "process(" in result.output


def test_call_mode_requires_call_function() -> None:
    """--mode call without --call-function gives a usage error."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-params",
            "x",
        ],
        input="[1]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code != 0
    assert "--call-function is required" in result.output


def test_call_mode_requires_call_params() -> None:
    """--mode call without --call-params gives a usage error."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-function",
            "foo",
        ],
        input="[1]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code != 0
    assert "--call-params is required" in result.output


def test_call_mode_javascript() -> None:
    """Call mode works with JavaScript (object-style calls)."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "javascript",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-function",
            "createUser",
            "--call-params",
            "name,age",
        ],
        input='[["alice", 30]]\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert "createUser(" in result.output


def test_call_mode_invalid_json() -> None:
    """Call mode surfaces JSON parse errors as CLI errors."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-function",
            "foo",
            "--call-params",
            "x",
        ],
        input="{bad json}\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_pre_indent_level_with_variable_name() -> None:
    """Pre-indent level uniformly offsets every line of a declaration."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--pre-indent-level",
            "1",
            "--variable-name",
            "data",
        ],
        input='{"a": 1, "b": [2, 3]}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, result.output
    expected = '    data = {\n        "a": 1,\n        "b": (2, 3),\n    }\n'
    assert result.output == expected


def test_heterogeneous_strategy_rust_tagged_enum() -> None:
    """--heterogeneous-strategy tagged_enum wraps Rust heterogeneous values."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "rust",
            "-f",
            "json",
            "--heterogeneous-strategy",
            "tagged_enum",
            "--variable-name",
            "data",
            "--include-preamble",
        ],
        input='[1, "a"]\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, result.output
    expected = (
        "enum Value {\n"
        "    I32(i32),\n"
        "    Str(&'static str),\n"
        "}\n"
        "let data = vec![\n"
        "    Value::I32(1),\n"
        '    Value::Str("a"),\n'
        "];\n"
    )
    assert result.output == expected


def test_heterogeneous_strategy_invalid_for_language() -> None:
    """Error when the strategy is not valid for the language."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--heterogeneous-strategy",
            "tagged_enum",
        ],
        input='[1, "a"]\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code != 0
    expected = (
        "Usage: literalize [OPTIONS]\n"
        "Try 'literalize --help' for help.\n"
        "\n"
        "Error: Invalid value 'tagged_enum' for "
        "--heterogeneous-strategy. Valid choices: error.\n"
    )
    assert result.output == expected


def test_call_mode_language_has_no_call_syntax() -> None:
    """Languages with no call syntax raise a clean CLI error."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "yaml",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-function",
            "foo",
            "--call-params",
            "x",
        ],
        input="[[1]]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert result.output == "Error: Yaml has no function call syntax\n"


def test_call_mode_not_implemented_for_language() -> None:
    """Languages without call rendering implemented raise a clean error."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "cobol",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-function",
            "foo",
            "--call-params",
            "x",
        ],
        input="[[1]]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    expected = (
        "Error: literalizer does not support "
        "function call rendering for Cobol\n"
    )
    assert result.output == expected


def test_call_mode_parameter_count_mismatch() -> None:
    """Mismatched --call-params count raises a clean CLI error."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-function",
            "foo",
            "--call-params",
            "x,y,z",
        ],
        input="[[1]]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert result.output == "Error: Expected 3 parameters but got 1 values\n"


def test_wrap_in_file() -> None:
    """--wrap-in-file wraps output as a complete source file."""
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
            "--wrap-in-file",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    assert "package main" in result.output
    assert "data" in result.output
