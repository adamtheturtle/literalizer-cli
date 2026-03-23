"""CLI for literalizer - convert data to native language literal syntax."""

import sys
from importlib.metadata import PackageNotFoundError, version

import click
from literalizer import literalize_json
from literalizer.languages import ALL_LANGUAGES

try:
    __version__ = version(distribution_name="literalizer-cli")
except PackageNotFoundError:  # pragma: no cover
    from ._setuptools_scm_version import __version__

_LANGUAGE_MAP = {
    lang_cls.__name__.lower(): lang_cls for lang_cls in ALL_LANGUAGES
}


@click.command(name="literalize")
@click.version_option(version=__version__)
@click.option(
    "--language",
    "-l",
    required=True,
    type=click.Choice(sorted(_LANGUAGE_MAP), case_sensitive=False),
    help="Target language for output.",
)
def main(language: str) -> None:
    """Convert data structures to native language literal syntax."""
    json_string = sys.stdin.read()
    lang_cls = _LANGUAGE_MAP[language]
    lang_instance = lang_cls()
    result = literalize_json(
        json_string=json_string,
        language=lang_instance,
        line_prefix="",
        indent="    ",
        include_delimiters=True,
        variable_name=None,
        new_variable=True,
        error_on_coercion=False,
    )
    click.echo(result)


if __name__ == "__main__":
    main()
