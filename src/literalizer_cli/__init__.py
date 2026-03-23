"""CLI for literalizer - convert data to native language literal syntax."""

import inspect
import sys
from importlib.metadata import PackageNotFoundError, version

import click
import literalizer.exceptions
from literalizer import literalize_json, literalize_yaml
from literalizer._language import Language, LanguageCls
from literalizer.languages import ALL_LANGUAGES

try:
    __version__ = version(distribution_name="literalizer-cli")
except PackageNotFoundError:  # pragma: no cover
    from ._setuptools_scm_version import __version__

_LANGUAGE_MAP = {
    lang_cls.__name__.lower(): lang_cls for lang_cls in ALL_LANGUAGES
}

_INPUT_FORMATS = ("json", "yaml")

_INDENT = "    "


def _get_language_init_params(
    lang_cls: LanguageCls,
) -> dict[str, inspect.Parameter]:
    """Get the public init parameters for a language class."""
    sig = inspect.signature(obj=lang_cls.__init__)  # type: ignore[misc]
    return {
        name: param
        for name, param in sig.parameters.items()
        if name != "self" and not name.startswith("_")
    }


def _all_choices_for_param(param_name: str) -> list[str]:
    """Collect all valid enum member names for a param across languages."""
    members: set[str] = set()
    for lang_cls in ALL_LANGUAGES:
        params = _get_language_init_params(lang_cls=lang_cls)
        if param_name in params:
            enum_cls = params[param_name].annotation
            members.update(m.lower() for m in enum_cls.__members__)
    return sorted(members)


def _choices_help(label: str, param_name: str) -> str:
    """Build a help string listing all choices for a language param."""
    choices = ", ".join(
        _all_choices_for_param(param_name=param_name),
    )
    return f"{label} (language-specific). Choices: {choices}."


_SEQUENCE_FORMAT_HELP = _choices_help(
    label="Sequence format",
    param_name="sequence_format",
)
_SET_FORMAT_HELP = _choices_help(
    label="Set format",
    param_name="set_format",
)
_DATE_FORMAT_HELP = _choices_help(
    label="Date format",
    param_name="date_format",
)
_DATETIME_FORMAT_HELP = _choices_help(
    label="Datetime format",
    param_name="datetime_format",
)
_BYTES_FORMAT_HELP = _choices_help(
    label="Bytes format",
    param_name="bytes_format",
)
_COMMENT_FORMAT_HELP = _choices_help(
    label="Comment format",
    param_name="comment_format",
)
_VARIABLE_TYPE_HINTS_HELP = _choices_help(
    label="Variable type hints",
    param_name="variable_type_hints",
)
_EMPTY_DICT_KEY_HELP = _choices_help(
    label="Empty dict key handling",
    param_name="empty_dict_key",
)


def _resolve_language_option(
    *,
    lang_cls: LanguageCls,
    option_name: str,
    value: str,
) -> object:
    """Resolve a CLI string value to a language enum member."""
    params = _get_language_init_params(lang_cls=lang_cls)
    if option_name not in params:
        lang_name = lang_cls.__name__.lower()
        raise click.UsageError(
            message=f"--{option_name.replace('_', '-')} is not supported "
            f"for language '{lang_name}'.",
        )
    enum_cls = params[option_name].annotation
    upper_value = value.upper()
    if upper_value not in enum_cls.__members__:
        choices = ", ".join(sorted(enum_cls.__members__))
        cli_name = option_name.replace("_", "-")
        raise click.UsageError(
            message=f"Invalid value '{value}' for "
            f"--{cli_name}. Valid choices: {choices}.",
        )
    return enum_cls[upper_value]


def literalize_input(
    *,
    input_string: str,
    language: Language,
    input_format: str,
    line_prefix: str,
    indent: str,
    include_delimiters: bool,
    variable_name: str | None,
    new_variable: bool,
    error_on_coercion: bool,
) -> str:
    """Literalize input and surface literalizer errors as CLI errors."""
    try:
        if input_format == "yaml":
            return literalize_yaml(
                yaml_string=input_string,
                language=language,
                line_prefix=line_prefix,
                indent=indent,
                include_delimiters=include_delimiters,
                variable_name=variable_name,
                new_variable=new_variable,
                error_on_coercion=error_on_coercion,
            )
        return literalize_json(
            json_string=input_string,
            language=language,
            line_prefix=line_prefix,
            indent=indent,
            include_delimiters=include_delimiters,
            variable_name=variable_name,
            new_variable=new_variable,
            error_on_coercion=error_on_coercion,
        )
    except literalizer.exceptions.JSONParseError as exc:
        raise click.ClickException(message=str(object=exc)) from None
    except literalizer.exceptions.YAMLParseError as exc:
        raise click.ClickException(message=str(object=exc)) from None
    except literalizer.exceptions.ParseError as exc:
        raise click.ClickException(message=str(object=exc)) from None
    except literalizer.exceptions.EmptyDictKeyError as exc:
        raise click.ClickException(message=str(object=exc)) from None
    except literalizer.exceptions.HeterogeneousCoercionError as exc:
        raise click.ClickException(message=str(object=exc)) from None
    except literalizer.exceptions.NullInCollectionError as exc:
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
    "--line-prefix",
    default="",
    help="Prefix for each output line.",
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
    "--error-on-coercion/--no-error-on-coercion",
    default=False,
    help="Error on heterogeneous type coercion.",
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
    "--empty-dict-key",
    default=None,
    help=_EMPTY_DICT_KEY_HELP,
)
def main(
    language: str,
    input_format: str,
    line_prefix: str,
    indent: str,
    include_delimiters: bool,  # noqa: FBT001
    variable_name: str | None,
    new_variable: bool,  # noqa: FBT001
    error_on_coercion: bool,  # noqa: FBT001
    sequence_format: str | None,
    set_format: str | None,
    date_format: str | None,
    datetime_format: str | None,
    bytes_format: str | None,
    comment_format: str | None,
    variable_type_hints: str | None,
    empty_dict_key: str | None,
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
        "empty_dict_key": empty_dict_key,
    }
    for option_name, value in cli_language_options.items():
        if value is not None:
            lang_kwargs[option_name] = _resolve_language_option(
                lang_cls=lang_cls,
                option_name=option_name,
                value=value,
            )

    lang_instance = lang_cls(**lang_kwargs)
    result = literalize_input(
        input_string=input_string,
        language=lang_instance,
        input_format=input_format,
        line_prefix=line_prefix,
        indent=indent,
        include_delimiters=include_delimiters,
        variable_name=variable_name,
        new_variable=new_variable,
        error_on_coercion=error_on_coercion,
    )
    click.echo(message=result)


if __name__ == "__main__":
    main()
