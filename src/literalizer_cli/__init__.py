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
    error_on_coercion: bool,
) -> str:
    """Literalize input and surface literalizer errors as CLI errors."""
    try:
        if input_format == "yaml":
            return literalize_yaml(
                yaml_string=input_string,
                language=language,
                line_prefix="",
                indent=_INDENT,
                include_delimiters=True,
                variable_name=None,
                new_variable=True,
                error_on_coercion=error_on_coercion,
            )
        return literalize_json(
            json_string=input_string,
            language=language,
            line_prefix="",
            indent=_INDENT,
            include_delimiters=True,
            variable_name=None,
            new_variable=True,
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
    type=click.Choice(sorted(_LANGUAGE_MAP), case_sensitive=False),
    help="Target language for output.",
)
@click.option(
    "--input-format",
    "-f",
    default="yaml",
    type=click.Choice(_INPUT_FORMATS, case_sensitive=False),
    help="Input data format.",
)
def main(language: str, input_format: str) -> None:
    """Convert data structures to native language literal syntax."""
    input_string = sys.stdin.read()
    lang_cls = _LANGUAGE_MAP[language]
    lang_instance = lang_cls()
    result = literalize_input(
        input_string=input_string,
        language=lang_instance,
        input_format=input_format,
        error_on_coercion=False,
    )
    click.echo(result)


if __name__ == "__main__":
    main()
