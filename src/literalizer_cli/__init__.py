"""CLI for literalizer - convert data to native language literal syntax."""

import enum
import sys
from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, version

import click
import literalizer.exceptions
from literalizer import (
    ExistingVariable,
    IdentifierCase,
    InputFormat,
    LiteralizeResult,
    NewVariable,
    VariableForm,
    literalize,
    literalize_call,
)
from literalizer._language import Language, LanguageCls
from literalizer.languages import ALL_LANGUAGES

try:
    __version__ = version(distribution_name="literalizer-cli")
except PackageNotFoundError:  # pragma: no cover
    from ._setuptools_scm_version import __version__

_LANGUAGE_MAP = {
    lang_cls.__name__.lower(): lang_cls for lang_cls in ALL_LANGUAGES
}

_INPUT_FORMATS = ("json", "json5", "yaml", "toml")

_INPUT_FORMAT_MAP: dict[str, InputFormat] = {
    "json": InputFormat.JSON,
    "json5": InputFormat.JSON5,
    "yaml": InputFormat.YAML,
    "toml": InputFormat.TOML,
}

_INDENT = "    "

_REF_CASE_MAP: dict[str, IdentifierCase] = {
    member.name.lower(): member for member in IdentifierCase
}

# Map from CLI option name to a getter for the enum class.
_OPTION_TO_ENUM: dict[str, Callable[[LanguageCls], type[enum.Enum]]] = {
    "sequence_format": lambda cls: cls.SequenceFormats,
    "set_format": lambda cls: cls.SetFormats,
    "date_format": lambda cls: cls.DateFormats,
    "datetime_format": lambda cls: cls.DatetimeFormats,
    "bytes_format": lambda cls: cls.BytesFormats,
    "comment_format": lambda cls: cls.CommentFormats,
    "variable_type_hints": lambda cls: cls.VariableTypeHints,
    "declaration_style": lambda cls: cls.DeclarationStyles,
    "dict_entry_style": lambda cls: cls.DictEntryStyles,
    "dict_format": lambda cls: cls.DictFormats,
    "float_format": lambda cls: cls.FloatFormats,
    "integer_format": lambda cls: cls.IntegerFormats,
    "numeric_literal_suffix": lambda cls: cls.NumericLiteralSuffixes,
    "numeric_separator": lambda cls: cls.NumericSeparators,
    "string_format": lambda cls: cls.StringFormats,
    "trailing_comma": lambda cls: cls.TrailingCommas,
    "empty_dict_key": lambda cls: cls.EmptyDictKey,
    "line_ending": lambda cls: cls.LineEndings,
    "heterogeneous_strategy": lambda cls: cls.HeterogeneousStrategies,
}


def _get_enum_for_option(
    *,
    lang_cls: LanguageCls,
    option_name: str,
) -> type[enum.Enum]:
    """Get the enum class for a language option."""
    return _OPTION_TO_ENUM[option_name](lang_cls)


def _all_choices_for_option(option_name: str) -> list[str]:
    """Collect all valid enum member names for an option."""
    members: set[str] = set()
    for lang_cls in ALL_LANGUAGES:
        enum_cls = _get_enum_for_option(
            lang_cls=lang_cls,
            option_name=option_name,
        )
        members.update(m.lower() for m in enum_cls.__members__)
    return sorted(members)


def _choices_help(label: str, option_name: str) -> str:
    """Build a help string listing all choices for a language option."""
    choices = ", ".join(
        _all_choices_for_option(option_name=option_name),
    )
    return f"{label} (language-specific). Choices: {choices}."


_SEQUENCE_FORMAT_HELP = _choices_help(
    label="Sequence format",
    option_name="sequence_format",
)
_SET_FORMAT_HELP = _choices_help(
    label="Set format",
    option_name="set_format",
)
_DATE_FORMAT_HELP = _choices_help(
    label="Date format",
    option_name="date_format",
)
_DATETIME_FORMAT_HELP = _choices_help(
    label="Datetime format",
    option_name="datetime_format",
)
_BYTES_FORMAT_HELP = _choices_help(
    label="Bytes format",
    option_name="bytes_format",
)
_COMMENT_FORMAT_HELP = _choices_help(
    label="Comment format",
    option_name="comment_format",
)
_VARIABLE_TYPE_HINTS_HELP = _choices_help(
    label="Variable type hints",
    option_name="variable_type_hints",
)
_DECLARATION_STYLE_HELP = _choices_help(
    label="Declaration style",
    option_name="declaration_style",
)
_DICT_ENTRY_STYLE_HELP = _choices_help(
    label="Dict entry style",
    option_name="dict_entry_style",
)
_DICT_FORMAT_HELP = _choices_help(
    label="Dict format",
    option_name="dict_format",
)
_FLOAT_FORMAT_HELP = _choices_help(
    label="Float format",
    option_name="float_format",
)
_INTEGER_FORMAT_HELP = _choices_help(
    label="Integer format",
    option_name="integer_format",
)
_NUMERIC_LITERAL_SUFFIX_HELP = _choices_help(
    label="Numeric literal suffix",
    option_name="numeric_literal_suffix",
)
_NUMERIC_SEPARATOR_HELP = _choices_help(
    label="Numeric separator",
    option_name="numeric_separator",
)
_STRING_FORMAT_HELP = _choices_help(
    label="String format",
    option_name="string_format",
)
_TRAILING_COMMA_HELP = _choices_help(
    label="Trailing comma",
    option_name="trailing_comma",
)
_EMPTY_DICT_KEY_HELP = _choices_help(
    label="Empty dict key handling",
    option_name="empty_dict_key",
)
_LINE_ENDING_HELP = _choices_help(
    label="Line ending style",
    option_name="line_ending",
)
_HETEROGENEOUS_STRATEGY_HELP = _choices_help(
    label="Heterogeneous-collection strategy",
    option_name="heterogeneous_strategy",
)


def _all_modifier_choices() -> list[str]:
    """Collect every modifier name across all languages."""
    members: set[str] = set()
    for lang_cls in ALL_LANGUAGES:
        members.update(m.lower() for m in lang_cls.Modifiers.__members__)
    return sorted(members)


_MODIFIER_HELP = (
    "Declaration modifier (language-specific, repeatable). "
    f"Choices: {', '.join(_all_modifier_choices())}."
)


def _resolve_modifiers(
    *,
    lang_cls: LanguageCls,
    values: tuple[str, ...],
) -> frozenset[enum.Enum]:
    """Resolve CLI modifier strings to the language's Modifiers members."""
    modifier_enum = lang_cls.Modifiers
    if not modifier_enum.__members__:
        lang_name = lang_cls.__name__.lower()
        raise click.UsageError(
            message=(
                f"--modifier is not supported for language '{lang_name}'."
            ),
        )
    resolved: set[enum.Enum] = set()
    for value in values:
        upper_value = value.upper()
        if upper_value not in modifier_enum.__members__:
            choices = ", ".join(
                sorted(m.lower() for m in modifier_enum.__members__),
            )
            raise click.UsageError(
                message=(
                    f"Invalid value '{value}' for --modifier. "
                    f"Valid choices: {choices}."
                ),
            )
        resolved.add(modifier_enum[upper_value])
    return frozenset(resolved)


# Language options that take a free-form string rather than an enum.
# Maps CLI option name to a getter for the ``supports_*`` flag.
_STRING_OPTIONS: dict[
    str,
    Callable[[LanguageCls], bool],
] = {
    "default_dict_key_type": (lambda cls: cls.supports_default_dict_key_type),
    "default_dict_value_type": (
        lambda cls: cls.supports_default_dict_value_type
    ),
    "default_sequence_element_type": (
        lambda cls: cls.supports_default_sequence_element_type
    ),
    "default_set_element_type": (
        lambda cls: cls.supports_default_set_element_type
    ),
    "default_ordered_map_value_type": (
        lambda cls: cls.supports_default_ordered_map_value_type
    ),
}


def _resolve_language_option(
    *,
    lang_cls: LanguageCls,
    option_name: str,
    value: str,
) -> enum.Enum:
    """Resolve a CLI string value to a language enum member."""
    enum_cls = _get_enum_for_option(
        lang_cls=lang_cls,
        option_name=option_name,
    )
    upper_value = value.upper()
    if upper_value not in enum_cls.__members__:
        choices = ", ".join(
            sorted(m.lower() for m in enum_cls.__members__),
        )
        cli_name = option_name.replace("_", "-")
        raise click.UsageError(
            message=f"Invalid value '{value}' for "
            f"--{cli_name}. Valid choices: {choices}.",
        )
    return enum_cls[upper_value]


_LITERALIZER_EXCEPTIONS = (
    literalizer.exceptions.JSONParseError,
    literalizer.exceptions.JSON5ParseError,
    literalizer.exceptions.YAMLParseError,
    literalizer.exceptions.TOMLParseError,
    literalizer.exceptions.InvalidDictKeyError,
    literalizer.exceptions.HeterogeneousCollectionError,
    literalizer.exceptions.NullInCollectionError,
    literalizer.exceptions.PerElementNotListError,
    literalizer.exceptions.ParameterCountMismatchError,
    literalizer.exceptions.CallsNotSupportedByLanguageError,
    literalizer.exceptions.CallsNotSupportedByToolError,
    literalizer.exceptions.IncompatibleFormatsError,
    literalizer.exceptions.UnrepresentableIntegerError,
    literalizer.exceptions.UnsupportedIdentifierCaseError,
)


def literalize_input(
    *,
    input_string: str,
    language: Language,
    input_format: InputFormat,
    pre_indent_level: int,
    include_delimiters: bool,
    variable_form: VariableForm | None,
    wrap_in_file: bool,
    ref_case: IdentifierCase | None,
) -> LiteralizeResult:
    """Literalize input and surface literalizer errors as CLI errors."""
    try:
        return literalize(
            source=input_string,
            input_format=input_format,
            language=language,
            pre_indent_level=pre_indent_level,
            include_delimiters=include_delimiters,
            variable_form=variable_form,
            wrap_in_file=wrap_in_file,
            ref_case=ref_case,
        )
    except _LITERALIZER_EXCEPTIONS as exc:
        raise click.ClickException(message=str(object=exc)) from None


def literalize_call_input(
    *,
    input_string: str,
    language: Language,
    input_format: InputFormat,
    target_function: str,
    parameter_names: tuple[str, ...],
    per_element: bool,
    wrap_in_file: bool,
    ref_case: IdentifierCase | None,
) -> LiteralizeResult:
    """Literalize input as function calls, surfacing errors as CLI errors."""
    try:
        return literalize_call(
            source=input_string,
            input_format=input_format,
            language=language,
            target_function=target_function,
            parameter_names=parameter_names,
            per_element=per_element,
            wrap_in_file=wrap_in_file,
            ref_case=ref_case,
        )
    except _LITERALIZER_EXCEPTIONS as exc:
        raise click.ClickException(message=str(object=exc)) from None


@click.command(name="literalize")
@click.version_option(version=__version__)
@click.option(
    "--language",
    "-l",
    required=True,
    type=click.Choice(choices=sorted(_LANGUAGE_MAP), case_sensitive=False),
    help="Target language for output.",
)
@click.option(
    "--input-format",
    "-f",
    default="yaml",
    type=click.Choice(choices=_INPUT_FORMATS, case_sensitive=False),
    help="Input data format.",
)
@click.option(
    "--pre-indent-level",
    default=0,
    type=int,
    help="Number of indent levels to prefix each output line with.",
)
@click.option(
    "--indent",
    default=_INDENT,
    help="Indentation string.",
)
@click.option(
    "--include-delimiters/--no-include-delimiters",
    default=True,
    help="Include opening/closing delimiters.",
)
@click.option(
    "--variable-name",
    default=None,
    help="Variable name for the output assignment.",
)
@click.option(
    "--new-variable/--no-new-variable",
    default=True,
    help="Declare a new variable.",
)
@click.option(
    "--modifier",
    "modifiers",
    multiple=True,
    help=_MODIFIER_HELP,
)
@click.option(
    "--wrap-in-file/--no-wrap-in-file",
    default=False,
    help="Wrap output as a complete, valid source file.",
)
@click.option(
    "--sequence-format",
    default=None,
    help=_SEQUENCE_FORMAT_HELP,
)
@click.option(
    "--set-format",
    default=None,
    help=_SET_FORMAT_HELP,
)
@click.option(
    "--date-format",
    default=None,
    help=_DATE_FORMAT_HELP,
)
@click.option(
    "--datetime-format",
    default=None,
    help=_DATETIME_FORMAT_HELP,
)
@click.option(
    "--bytes-format",
    default=None,
    help=_BYTES_FORMAT_HELP,
)
@click.option(
    "--comment-format",
    default=None,
    help=_COMMENT_FORMAT_HELP,
)
@click.option(
    "--variable-type-hints",
    default=None,
    help=_VARIABLE_TYPE_HINTS_HELP,
)
@click.option(
    "--declaration-style",
    default=None,
    help=_DECLARATION_STYLE_HELP,
)
@click.option(
    "--dict-entry-style",
    default=None,
    help=_DICT_ENTRY_STYLE_HELP,
)
@click.option(
    "--dict-format",
    default=None,
    help=_DICT_FORMAT_HELP,
)
@click.option(
    "--float-format",
    default=None,
    help=_FLOAT_FORMAT_HELP,
)
@click.option(
    "--integer-format",
    default=None,
    help=_INTEGER_FORMAT_HELP,
)
@click.option(
    "--numeric-literal-suffix",
    default=None,
    help=_NUMERIC_LITERAL_SUFFIX_HELP,
)
@click.option(
    "--numeric-separator",
    default=None,
    help=_NUMERIC_SEPARATOR_HELP,
)
@click.option(
    "--string-format",
    default=None,
    help=_STRING_FORMAT_HELP,
)
@click.option(
    "--trailing-comma",
    default=None,
    help=_TRAILING_COMMA_HELP,
)
@click.option(
    "--empty-dict-key",
    default=None,
    help=_EMPTY_DICT_KEY_HELP,
)
@click.option(
    "--line-ending",
    default=None,
    help=_LINE_ENDING_HELP,
)
@click.option(
    "--heterogeneous-strategy",
    default=None,
    help=_HETEROGENEOUS_STRATEGY_HELP,
)
@click.option(
    "--default-dict-key-type",
    default=None,
    help="Default type for dict keys (language-specific, free-form string).",
)
@click.option(
    "--default-dict-value-type",
    default=None,
    help=(
        "Default type for dict values (language-specific, free-form string)."
    ),
)
@click.option(
    "--default-sequence-element-type",
    default=None,
    help=(
        "Default type for sequence elements"
        " (language-specific, free-form string)."
    ),
)
@click.option(
    "--default-set-element-type",
    default=None,
    help=(
        "Default type for set elements (language-specific, free-form string)."
    ),
)
@click.option(
    "--default-ordered-map-value-type",
    default=None,
    help=(
        "Default type for ordered map values"
        " (language-specific, free-form string)."
    ),
)
@click.option(
    "--include-preamble/--no-include-preamble",
    default=False,
    help="Include language preamble (e.g. package declarations, imports).",
)
@click.option(
    "--mode",
    default="literal",
    type=click.Choice(choices=("literal", "call"), case_sensitive=False),
    help="Output mode: 'literal' for data literals,"
    " 'call' for function calls.",
)
@click.option(
    "--call-function",
    default=None,
    help="Function name for call mode (e.g. 'create_user').",
)
@click.option(
    "--call-params",
    default=None,
    help="Comma-separated parameter names for call mode.",
)
@click.option(
    "--per-element/--no-per-element",
    default=True,
    help="In call mode, each top-level list element becomes a separate call.",
)
@click.option(
    "--ref-case",
    default=None,
    type=click.Choice(choices=sorted(_REF_CASE_MAP), case_sensitive=False),
    help=(
        "Identifier case for ``$ref`` markers in input data. When set, "
        'objects of the form ``{"$ref": "name"}`` are emitted as '
        "bare identifiers re-cased to the chosen convention instead of "
        "as nested dicts."
    ),
)
def main(
    *,
    language: str,
    input_format: str,
    pre_indent_level: int,
    indent: str,
    include_delimiters: bool,
    variable_name: str | None,
    new_variable: bool,
    modifiers: tuple[str, ...],
    wrap_in_file: bool,
    sequence_format: str | None,
    set_format: str | None,
    date_format: str | None,
    datetime_format: str | None,
    bytes_format: str | None,
    comment_format: str | None,
    variable_type_hints: str | None,
    declaration_style: str | None,
    dict_entry_style: str | None,
    dict_format: str | None,
    float_format: str | None,
    integer_format: str | None,
    numeric_literal_suffix: str | None,
    numeric_separator: str | None,
    string_format: str | None,
    trailing_comma: str | None,
    empty_dict_key: str | None,
    line_ending: str | None,
    heterogeneous_strategy: str | None,
    default_dict_key_type: str | None,
    default_dict_value_type: str | None,
    default_sequence_element_type: str | None,
    default_set_element_type: str | None,
    default_ordered_map_value_type: str | None,
    include_preamble: bool,
    mode: str,
    call_function: str | None,
    call_params: str | None,
    per_element: bool,
    ref_case: str | None,
) -> None:
    """Convert data structures to native language literal syntax."""
    input_string = sys.stdin.read()
    lang_cls = _LANGUAGE_MAP[language]

    lang_kwargs: dict[str, object] = {}
    cli_language_options = {
        "sequence_format": sequence_format,
        "set_format": set_format,
        "date_format": date_format,
        "datetime_format": datetime_format,
        "bytes_format": bytes_format,
        "comment_format": comment_format,
        "variable_type_hints": variable_type_hints,
        "declaration_style": declaration_style,
        "dict_entry_style": dict_entry_style,
        "dict_format": dict_format,
        "float_format": float_format,
        "integer_format": integer_format,
        "numeric_literal_suffix": numeric_literal_suffix,
        "numeric_separator": numeric_separator,
        "string_format": string_format,
        "trailing_comma": trailing_comma,
        "empty_dict_key": empty_dict_key,
        "line_ending": line_ending,
        "heterogeneous_strategy": heterogeneous_strategy,
    }
    for option_name, value in cli_language_options.items():
        if value is not None:
            lang_kwargs[option_name] = _resolve_language_option(
                lang_cls=lang_cls,
                option_name=option_name,
                value=value,
            )

    cli_string_options = {
        "default_dict_key_type": default_dict_key_type,
        "default_dict_value_type": default_dict_value_type,
        "default_sequence_element_type": default_sequence_element_type,
        "default_set_element_type": default_set_element_type,
        "default_ordered_map_value_type": default_ordered_map_value_type,
    }
    for option_name, value in cli_string_options.items():
        if value is not None:
            if not _STRING_OPTIONS[option_name](lang_cls):
                lang_name = lang_cls.__name__.lower()
                raise click.UsageError(
                    message=(
                        f"--{option_name.replace('_', '-')} is not "
                        f"supported for language '{lang_name}'."
                    ),
                )
            lang_kwargs[option_name] = value

    lang_instance = lang_cls(indent=indent, **lang_kwargs)

    variable_form: VariableForm | None = None
    if variable_name is not None:
        if new_variable:
            resolved_modifiers: frozenset[enum.Enum] = (
                _resolve_modifiers(lang_cls=lang_cls, values=modifiers)
                if modifiers
                else frozenset()
            )
            variable_form = NewVariable(
                name=variable_name,
                modifiers=resolved_modifiers,
            )
        else:
            if modifiers:
                raise click.UsageError(
                    message=(
                        "--modifier cannot be used with --no-new-variable."
                    ),
                )
            variable_form = ExistingVariable(name=variable_name)
    elif modifiers:
        raise click.UsageError(
            message="--modifier requires --variable-name.",
        )

    resolved_ref_case = (
        _REF_CASE_MAP[ref_case.lower()] if ref_case is not None else None
    )

    if mode == "call":
        if call_function is None:
            raise click.UsageError(
                message="--call-function is required in call mode.",
            )
        if call_params is None:
            raise click.UsageError(
                message="--call-params is required in call mode.",
            )
        parsed_params = tuple(
            p.strip() for p in call_params.split(sep=",") if p.strip()
        )
        result = literalize_call_input(
            input_string=input_string,
            language=lang_instance,
            input_format=_INPUT_FORMAT_MAP[input_format],
            target_function=call_function,
            parameter_names=parsed_params,
            per_element=per_element,
            wrap_in_file=wrap_in_file,
            ref_case=resolved_ref_case,
        )
    else:
        result = literalize_input(
            input_string=input_string,
            language=lang_instance,
            input_format=_INPUT_FORMAT_MAP[input_format],
            pre_indent_level=pre_indent_level,
            include_delimiters=include_delimiters,
            variable_form=variable_form,
            wrap_in_file=wrap_in_file,
            ref_case=resolved_ref_case,
        )
    if include_preamble:
        for preamble_line in result.preamble:
            click.echo(message=preamble_line)
    click.echo(message=result.code)
