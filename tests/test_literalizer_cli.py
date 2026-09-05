"""Tests for literalizer_cli."""

import inspect
import runpy
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import literalizer.exceptions
import pytest
from click import ClickException
from click.testing import CliRunner
from literalizer import ExistingVariable, InputFormat, NewVariable
from literalizer.languages import Go, Java, Python, R, Rust
from pytest_regressions.file_regression import FileRegressionFixture

import literalizer_cli
from literalizer_cli import main

_USAGE_ERROR_EXIT_CODE = 2
"""Click's exit code for a ``UsageError``."""

_MAX_PRE_INDENT_LEVEL = 100
"""Mirrors the bound on ``--pre-indent-level``."""


@dataclass(frozen=True, kw_only=True)
class ExceptionCase:
    """A real literalizer failure case and its expected CLI message."""

    input_format: InputFormat
    input_string: str
    language: Any
    expected: str
    variable_form: NewVariable | ExistingVariable | None


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


def test_literalize_yaml_non_string_dict_keys() -> None:
    """YAML non-string dict keys flow through to the target language."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--language", "python", "--input-format", "yaml"],
        input="1: a\n2: b\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected = textwrap.dedent(
        text="""\
        {
            1: "a",
            2: "b",
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
    """An unsupported ref-case for the language exits with a clean
    error.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "--language",
            "bash",
            "--input-format",
            "json",
            "--ref-case",
            "kebab",
        ],
        input='{"a": {"$ref": "userId"}}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert (
        result.output
        == "Error: Bash does not support identifier case 'KEBAB'\n"
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


def test_wrap_in_file_without_variable_unsupported() -> None:
    """Strict-typed langs reject ``--wrap-in-file`` without a variable."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "rust",
            "-f",
            "json",
            "--wrap-in-file",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    expected = (
        "Error: Rust cannot wrap a bare value"
        " (without a variable_form) at file scope\n"
    )
    assert result.output == expected


def test_variable_name_unsupported_for_language() -> None:
    """Data-format languages reject ``--variable-name``."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "yaml",
            "-f",
            "json",
            "--variable-name",
            "data",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    expected = "Error: Yaml does not support variable names: 'data'\n"
    assert result.output == expected


def test_dotted_call_target_unsupported_for_language() -> None:
    """HCL rejects dotted ``--call-function`` targets."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "hcl",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-function",
            "a.b",
            "--call-params",
            "x",
        ],
        input="[[1]]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    expected = "Error: Hcl does not support dotted call targets: 'a.b'\n"
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
            variable_form=None,
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
            variable_form=None,
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
            variable_form=None,
        ),
        ExceptionCase(
            input_format=InputFormat.JSON,
            input_string='{"a": }\n',
            language=Python(),
            expected="Invalid JSON: Expecting value at line 1 column 7",
            variable_form=None,
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
            variable_form=None,
        ),
        ExceptionCase(
            input_format=InputFormat.YAML,
            input_string="1: a\n2: b\n",
            language=Go(),
            expected="Go cannot represent dict key of type int",
            variable_form=None,
        ),
    ],
    ids=(
        "empty_dict_key",
        "heterogeneous_collection",
        "null_in_collection",
        "json_parse",
        "yaml_parse",
        "unrepresentable_non_string_dict_key",
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
            ref_key="$ref",
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


def test_multiline_string_format_with_cpp_delimiter_base() -> None:
    """C++ multi-line strings use the configured delimiter after a
    collision.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "cpp",
            "-f",
            "json",
            "--string-format",
            "multiline",
            "--multiline-raw-string-delimiter-base",
            "custom",
        ],
        input=r'"first )\"\nsecond"' "\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.output == 'R"custom(first )"\nsecond)custom"\n'


def test_invalid_cpp_multiline_raw_string_delimiter_base() -> None:
    """Invalid C++ raw-string delimiter bases are clean CLI errors."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "cpp",
            "-f",
            "json",
            "--multiline-raw-string-delimiter-base",
            "bad delimiter",
        ],
        input='"value"\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert result.output == (
        "Error: Cpp multiline_raw_string_delimiter_base 'bad delimiter' is "
        "invalid: these characters are not permitted by C++'s raw-string "
        "delimiter grammar: [' ']\n"
    )


def test_cpp_multiline_raw_string_delimiter_base_unsupported() -> None:
    """The C++ delimiter option rejects unsupported languages."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--multiline-raw-string-delimiter-base",
            "custom",
        ],
        input='"value"\n',
        catch_exceptions=False,
        color=True,
    )
    expected_usage_error_exit_code = 2
    assert result.exit_code == expected_usage_error_exit_code
    assert (
        "--multiline-raw-string-delimiter-base is not supported for "
        "language 'python'" in result.output
    )


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


def test_statement_terminator_style() -> None:
    """--statement-terminator-style controls trailing terminator
    emission.
    """
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
            "--statement-terminator-style",
            "none",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0
    # With statement_terminator_style=none, JavaScript omits the
    # trailing semicolon.
    assert ";" not in result.output


def test_call_style_curried_haskell() -> None:
    """--call-style curried emits curried Haskell applications."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "haskell",
            "-f",
            "json",
            "--mode",
            "call",
            "--call-function",
            "process",
            "--call-params",
            "x,y",
            "--call-style",
            "curried",
        ],
        input="[[1, 2]]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.output.rstrip().endswith("process (1) (2)")


def test_call_style_unsupported_for_language() -> None:
    """--call-style rejects languages whose constructor lacks the
    option.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "yaml",
            "-f",
            "json",
            "--call-style",
            "positional",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    expected_usage_error_exit_code = 2
    assert result.exit_code == expected_usage_error_exit_code
    assert "--call-style is not supported for language 'yaml'" in result.output


def test_module_name() -> None:
    """--module-name controls the wrap-in-file scope name."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "java",
            "-f",
            "json",
            "--wrap-in-file",
            "--module-name",
            "MyMod",
            "--variable-name",
            "data",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert "class MyMod {" in result.output


def test_module_name_unsupported_for_language() -> None:
    """--module-name rejects languages whose wrapper has no named
    scope.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--module-name",
            "MyMod",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    expected_usage_error_exit_code = 2
    assert result.exit_code == expected_usage_error_exit_code
    assert (
        "--module-name is not supported for language 'python'" in result.output
    )


def test_language_version() -> None:
    """--language-version selects a target version for the language."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--language-version",
            "py39",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    expected = textwrap.dedent(
        text="""\
        {
            "a": 1,
        }
    """
    )
    assert result.output == expected


def test_ref_key() -> None:
    """--ref-key selects a different marker key for $ref-style entries."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--ref-key",
            "_ref",
            "--ref-case",
            "snake",
        ],
        input='{"a": {"_ref": "user_id"}}\n',
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
    """--default-set-element-type overrides the default set element
    type.
    """
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
    """Error when a default type option is not supported for the
    language.
    """
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
    """Error when --modifier is given a value the language does not
    support.
    """
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


def test_call_mode_variable_name_new_variable() -> None:
    """``--variable-name`` in call mode wraps the call in a
    declaration.
    """
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
            "name",
            "--no-per-element",
            "--variable-name",
            "user",
        ],
        input='{"name": "alice"}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, result.output
    expected = 'const user = createUser({ name: {"name": "alice"} });\n'
    assert result.output == expected


def test_call_mode_variable_name_existing_variable() -> None:
    """``--no-new-variable`` in call mode emits a bare assignment."""
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
            "name",
            "--no-per-element",
            "--variable-name",
            "user",
            "--no-new-variable",
        ],
        input='{"name": "alice"}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, result.output
    assert result.output == 'user = create_user(name={"name": "alice"})\n'


def test_call_mode_variable_name_unsupported_shape() -> None:
    """An unsupported call/binding shape raises a clean error.

    ``--variable-name`` with multiple per-element calls cannot bind to a
    single variable name, so ``literalizer`` rejects the combination; the CLI
    surfaces it as a clean error rather than a traceback.
    """
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
            "name",
            "--per-element",
            "--variable-name",
            "user",
        ],
        input='[{"name": "alice"}, {"name": "bob"}]\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert result.output == (
        "Error: Python cannot represent this call shape: variable_form "
        "binds a single call result, but this input produces 2 calls; "
        "supply exactly one call (per_element=False, or per_element=True "
        "with a single-element source)\n"
    )


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
    """--heterogeneous-strategy tagged_enum wraps Rust heterogeneous
    values.
    """
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
        "--heterogeneous-strategy. Valid choices: error, record.\n"
    )
    assert result.output == expected


def test_record_struct_name_prefix() -> None:
    """--record-struct-name-prefix names the generated RECORD structs."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "rust",
            "-f",
            "json",
            "--heterogeneous-strategy",
            "record",
            "--record-struct-name-prefix",
            "Widget",
            "--variable-name",
            "data",
            "--include-preamble",
        ],
        input='{"id": 1, "label": "x"}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, result.output
    expected = (
        "struct Widget0 {\n"
        "    id: i32,\n"
        "    label: &'static str,\n"
        "}\n"
        "let data = Widget0 {\n"
        "    id: 1,\n"
        '    label: "x",\n'
        "};\n"
    )
    assert result.output == expected


def test_record_struct_name_prefix_invalid() -> None:
    """An invalid struct-name prefix surfaces as a clean CLI error."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "rust",
            "-f",
            "json",
            "--heterogeneous-strategy",
            "record",
            "--record-struct-name-prefix",
            "bad-name",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    expected = (
        "Error: record_struct_name_prefix 'bad-name' must be a PascalCase "
        "identifier starting with an uppercase letter.\n"
    )
    assert result.output == expected


def test_record_struct_name_prefix_unsupported_for_language() -> None:
    """--record-struct-name-prefix rejects languages without the
    option.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "yaml",
            "-f",
            "json",
            "--record-struct-name-prefix",
            "Widget",
        ],
        input='{"a": 1}\n',
        catch_exceptions=False,
        color=True,
    )
    expected_usage_error_exit_code = 2
    assert result.exit_code == expected_usage_error_exit_code
    expected = (
        "Usage: literalize [OPTIONS]\n"
        "Try 'literalize --help' for help.\n"
        "\n"
        "Error: --record-struct-name-prefix is not supported for "
        "language 'yaml'.\n"
    )
    assert result.output == expected


def test_cpp14_heterogeneous_value_variant_name() -> None:
    """C++14 carriers can be named through the CLI."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "cpp",
            "-f",
            "json",
            "--language-version",
            "cpp14",
            "--heterogeneous-strategy",
            "error",
            "--heterogeneous-value-variant-name",
            "DynamicValue",
            "--include-preamble",
        ],
        input='[1, "a"]\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, result.output
    assert "struct DynamicValue {" in result.output
    assert "std::vector<DynamicValue>{" in result.output


def test_heterogeneous_value_variant_name_unsupported() -> None:
    """Carrier names reject languages without the constructor option."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--heterogeneous-value-variant-name",
            "Value",
        ],
        input="1\n",
        catch_exceptions=False,
        color=True,
    )
    expected_usage_error_exit_code = 2
    assert result.exit_code == expected_usage_error_exit_code
    assert result.output.endswith(
        "Error: --heterogeneous-value-variant-name is not supported for "
        "language 'python'.\n"
    )


@pytest.mark.parametrize(
    argnames=("variable_name", "reason"),
    argvalues=[
        ("class", "it is a reserved identifier"),
        ("bad-name", "it is not a valid identifier"),
    ],
)
def test_invalid_new_variable_name(
    variable_name: str,
    reason: str,
) -> None:
    """Invalid new variable names surface as clean CLI errors."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--variable-name",
            variable_name,
        ],
        input="1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert result.output == (
        f"Error: Python cannot use NewVariable name {variable_name!r}: "
        f"{reason}\n"
    )


def test_tuple_arity_not_representable() -> None:
    """A tuple arity with no native form surfaces as a clean CLI error."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "kotlin",
            "-f",
            "json",
            "--heterogeneous-strategy",
            "tuple",
        ],
        input='[1, "a", true, 2, 3]\n',
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    expected = (
        "Error: a heterogeneous scalar array of 5 elements has no native "
        "fixed-size tuple in the target language\n"
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
    """Languages without call rendering implemented raise a clean
    error.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "nix",
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
        "Error: literalizer does not support function call rendering for Nix\n"
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


def test_python_union_format() -> None:
    """Python annotation and union options reach literalizer."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "--language",
            "python",
            "--input-format",
            "yaml",
            "--variable-name",
            "my_data",
            "--wrap-in-file",
            "--variable-type-hints",
            "always",
            "--annotation-evaluation",
            "postponed",
            "--union-format",
            "typing",
        ],
        input="- hello\n- 42\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.output == (
        "from __future__ import annotations\n"
        "from typing import Union\n"
        "my_data: tuple[Union[str, int], ...] = (\n"
        '    "hello",\n'
        "    42,\n"
        ")\n"
    )


def test_library_exception_not_in_a_hand_maintained_list() -> None:
    """An exception the CLI never enumerated is still a clean CLI error.

    ``UnrepresentableEmptyDictError`` is one of the 32 ``LiteralizerError``
    subclasses that the old hand-maintained tuple omitted, so it escaped as a
    Python traceback.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--language", "lua", "--input-format", "json"],
        input="{}\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert result.output.startswith("Error: ")
    assert "Traceback" not in result.output


def test_language_construction_failure_is_a_clean_error() -> None:
    """A constructor rejection is reported as a CLI error, not a traceback.

    Language construction happens outside ``literalize_input``, and was guarded
    by a separate two-entry tuple, so ``InvalidModuleNameError`` escaped.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--language", "java", "--module-name", "123 bad"],
        input="a: 1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 1
    assert result.output.startswith("Error: ")
    assert "Traceback" not in result.output


def test_every_library_exception_is_caught() -> None:
    """Every ``literalizer`` exception derives from the caught base class.

    Guards the regression directly: if the library grows an exception outside
    the hierarchy, the CLI would leak it as a traceback again.
    """
    subclasses = [
        obj
        for obj in vars(literalizer.exceptions).values()
        if inspect.isclass(object=obj)
        and issubclass(obj, Exception)
        and obj is not literalizer.exceptions.LiteralizerError
    ]
    assert subclasses
    uncaught = [
        obj.__name__
        for obj in subclasses
        if not issubclass(obj, literalizer.exceptions.LiteralizerError)
    ]
    assert not uncaught


@pytest.mark.parametrize(
    argnames=("args", "expected"),
    argvalues=[
        pytest.param(
            ["-l", "python", "--call-function", "f"],
            "--call-function has no effect in literal mode.",
            id="call-function-in-literal-mode",
        ),
        pytest.param(
            ["-l", "python", "--call-params", "x"],
            "--call-params has no effect in literal mode.",
            id="call-params-in-literal-mode",
        ),
        pytest.param(
            ["-l", "python", "--per-element"],
            "--per-element has no effect in literal mode.",
            id="per-element-in-literal-mode",
        ),
    ],
)
def test_call_options_rejected_in_literal_mode(
    args: list[str],
    expected: str,
) -> None:
    """Call-mode options are refused rather than silently ignored."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=args,
        input="a: 1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == _USAGE_ERROR_EXIT_CODE
    assert expected in result.output


@pytest.mark.parametrize(
    argnames=("extra", "expected"),
    argvalues=[
        pytest.param(
            ["--pre-indent-level", "3"],
            "--pre-indent-level has no effect in call mode.",
            id="pre-indent-level",
        ),
        pytest.param(
            ["--no-include-delimiters"],
            "--include-delimiters has no effect in call mode.",
            id="include-delimiters",
        ),
    ],
)
def test_literal_options_rejected_in_call_mode(
    extra: list[str],
    expected: str,
) -> None:
    """Literal-mode options are refused rather than silently ignored."""
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
            "f",
            "--call-params",
            "x",
            *extra,
        ],
        input="[[1]]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == _USAGE_ERROR_EXIT_CODE
    assert expected in result.output


def test_no_new_variable_requires_variable_name() -> None:
    """``--no-new-variable`` alone is a mistake, not a silent no-op."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "python", "--no-new-variable"],
        input="a: 1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == _USAGE_ERROR_EXIT_CODE
    assert "--no-new-variable requires --variable-name." in result.output


def test_default_valued_options_are_not_rejected() -> None:
    """A mode-specific default must not be mistaken for an explicit value.

    ``--pre-indent-level`` defaults to 0 and ``--include-delimiters`` to
    True, so call mode has to check how the value arrived, not what it is.
    """
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
            "f",
            "--call-params",
            "x",
        ],
        input="[[1]]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.output == "f(x=1)\n"


@pytest.mark.parametrize(
    argnames=("args", "expected"),
    argvalues=[
        pytest.param(
            ["--indent", ""],
            "--indent cannot be empty.",
            id="empty-indent",
        ),
        pytest.param(
            ["--indent", "\n"],
            "--indent cannot contain a line break.",
            id="newline-indent",
        ),
        pytest.param(
            ["--indent", "\r"],
            "--indent cannot contain a line break.",
            id="carriage-return-indent",
        ),
        pytest.param(
            ["--ref-key", ""],
            "--ref-key cannot be empty or whitespace.",
            id="empty-ref-key",
        ),
        pytest.param(
            ["--ref-key", "   "],
            "--ref-key cannot be empty or whitespace.",
            id="whitespace-ref-key",
        ),
    ],
)
def test_formatting_options_rejected(args: list[str], expected: str) -> None:
    """Values that would emit malformed output are refused."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "python", *args],
        input="a: 1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == _USAGE_ERROR_EXIT_CODE
    assert expected in result.output


@pytest.mark.parametrize(
    argnames="level",
    argvalues=["-1", "101", "100000"],
    ids=["negative", "just-over-maximum", "huge"],
)
def test_pre_indent_level_is_bounded(level: str) -> None:
    """Each level repeats the indent on every line, so the range is
    bounded.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "python", "--pre-indent-level", level],
        input="a: 1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == _USAGE_ERROR_EXIT_CODE


def test_pre_indent_level_upper_bound_is_allowed() -> None:
    """The bound itself is a valid value."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "--pre-indent-level",
            str(object=_MAX_PRE_INDENT_LEVEL),
        ],
        input="a: 1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)


@pytest.mark.parametrize(
    argnames="call_params",
    argvalues=["", "   ", ",,", " , , "],
    ids=["empty", "whitespace", "commas", "commas-and-spaces"],
)
def test_call_params_naming_nothing_is_rejected(call_params: str) -> None:
    """A value that names no parameter is reported as such.

    Falling through left the arity check to say "Expected 0 parameters but
    got 1 values", which describes the consequence rather than the mistake.
    """
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
            "f",
            "--call-params",
            call_params,
        ],
        input="[[1]]\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == _USAGE_ERROR_EXIT_CODE
    assert "--call-params must name at least one parameter." in result.output


@pytest.mark.parametrize(
    argnames="input_format",
    argvalues=["json", "yaml", "toml"],
)
@pytest.mark.parametrize(
    argnames="data",
    argvalues=["", "   \n  "],
    ids=["empty", "whitespace"],
)
def test_empty_input_is_rejected(input_format: str, data: str) -> None:
    """Empty input is refused the same way whatever the format.

    JSON already failed to parse it. YAML produced ``None`` and TOML an
    empty dict, so the same empty stdin gave three different answers.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "python", "-f", input_format],
        input=data,
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == _USAGE_ERROR_EXIT_CODE
    assert "No input data on stdin." in result.output


@pytest.mark.parametrize(
    argnames=("input_format", "data"),
    argvalues=[
        ("json", '﻿{"a": 1}\n'),
        ("yaml", "﻿a: 1\n"),
    ],
    ids=["json", "yaml"],
)
def test_byte_order_mark_is_stripped(input_format: str, data: str) -> None:
    """A leading BOM is a decoding artifact, not data.

    Windows editors and some HTTP clients add one. The parsers here read
    already-decoded text, so the mark reached them as content.
    """
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "python", "-f", input_format],
        input=data,
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.output == '{\n    "a": 1,\n}\n'


def test_duplicate_modifier_is_rejected() -> None:
    """A repeated modifier collapsed into the set with no feedback."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "java",
            "--variable-name",
            "x",
            "--modifier",
            "final",
            "--modifier",
            "final",
        ],
        input="a: 1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == _USAGE_ERROR_EXIT_CODE
    assert "--modifier final is given more than once." in result.output


def test_include_preamble_without_a_preamble_warns() -> None:
    """Asking for a preamble that does not exist says so on stderr."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["-l", "python", "--include-preamble"],
        input="a: 1\n",
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert "has no preamble" in result.output


def test_version_reports_the_library_too() -> None:
    """The library decides what the output looks like, so name it."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=["--version"],
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert "(literalizer " in result.output


def test_wrapper_does_not_run_on_import() -> None:
    """The wrapper script only runs when executed.

    Without a ``__main__`` guard, importing it ran the CLI, which reads
    stdin and exits.
    """
    wrapper = Path(__file__).parent.parent / "bin" / "literalize-wrapper.py"
    namespace = runpy.run_path(
        path_name=str(object=wrapper),
        run_name="not_main",
    )

    assert "main" in namespace


def test_input_file_is_read_instead_of_stdin(tmp_path: Path) -> None:
    """Input can come from a path, which is awkward to pipe on Windows."""
    source = tmp_path / "data.json"
    source.write_text(data='{"a": 1}', encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--input-file",
            str(object=source),
        ],
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert result.output == '{\n    "a": 1,\n}\n'


def test_empty_input_file_names_the_file(tmp_path: Path) -> None:
    """The message points at the file, not at stdin."""
    source = tmp_path / "empty.json"
    source.write_text(data="", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--input-file",
            str(object=source),
        ],
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == _USAGE_ERROR_EXIT_CODE
    assert f"No input data on {source}." in result.output


def test_missing_input_file_is_rejected(tmp_path: Path) -> None:
    """A path that does not exist fails before anything is read."""
    runner = CliRunner()
    result = runner.invoke(
        cli=main,
        args=[
            "-l",
            "python",
            "-f",
            "json",
            "--input-file",
            str(object=tmp_path / "absent.json"),
        ],
        catch_exceptions=False,
        color=True,
    )
    assert result.exit_code == _USAGE_ERROR_EXIT_CODE
    assert "does not exist" in result.output
