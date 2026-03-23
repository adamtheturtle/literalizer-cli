"""CLI for literalizer - convert data to native language literal syntax."""

import sys
from importlib.metadata import PackageNotFoundError, version

import click
from literalizer import literalize_json
from literalizer.languages import Python

try:
    __version__ = version(distribution_name="literalizer-cli")
except PackageNotFoundError:  # pragma: no cover
    from ._setuptools_scm_version import __version__


@click.command(name="literalize")
@click.version_option(version=__version__)
def main() -> None:
    """Convert data structures to native language literal syntax."""
    json_string = sys.stdin.read()
    language = Python(
        sequence_format=Python.sequence_formats.LIST,
    )
    language.format_string = repr
    result = literalize_json(
        json_string=json_string,
        language=language,
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
