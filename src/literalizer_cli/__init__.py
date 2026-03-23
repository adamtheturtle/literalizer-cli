"""CLI for literalizer - convert data to native language literal syntax."""

from importlib.metadata import PackageNotFoundError, version

import click

try:
    __version__ = version(distribution_name="literalizer-cli")
except PackageNotFoundError:  # pragma: no cover
    from ._setuptools_scm_version import __version__


@click.command(name="literalize")
@click.version_option(version=__version__)
def main() -> None:
    """Convert data structures to native language literal syntax."""
    click.echo("literalizer-cli")


if __name__ == "__main__":
    main()
