"""CLI for literalizer - convert data to native language literal syntax."""

import sys
from importlib.metadata import PackageNotFoundError, version

import click
import literalizer.exceptions
from literalizer import literalize_json, literalize_yaml
from literalizer._language import Language
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
        raise click.ClickException(message=str(exc)) from None
    except literalizer.exceptions.YAMLParseError as exc:
        raise click.ClickException(message=str(exc)) from None
    except literalizer.exceptions.ParseError as exc:
        raise click.ClickException(message=str(exc)) from None
    except literalizer.exceptions.EmptyDictKeyError as exc:
        raise click.ClickException(message=str(exc)) from None
    except literalizer.exceptions.HeterogeneousCoercionError as exc:
        raise click.ClickException(message=str(exc)) from None
    except literalizer.exceptions.NullInCollectionError as exc:
        raise click.ClickException(message=str(exc)) from None


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
def main(
    language: str,
    input_format: str,
    line_prefix: str,
    indent: str,
    include_delimiters: bool,  # noqa: FBT001
    variable_name: str | None,
    new_variable: bool,  # noqa: FBT001
    error_on_coercion: bool,  # noqa: FBT001
) -> None:
    """Convert data structures to native language literal syntax."""
    input_string = sys.stdin.read()
    lang_cls = _LANGUAGE_MAP[language]
    lang_instance = lang_cls()
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
