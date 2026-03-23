|Build Status| |PyPI|

literalizer-cli
================

CLI for literalizer - convert data structures to native language literal syntax.

.. contents::
   :local:

Installation
------------

With ``pip``
^^^^^^^^^^^^

Requires Python |minimum-python-version|\+.

.. code-block:: shell

   pip install literalizer-cli

With Homebrew (macOS, Linux, WSL)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Requires `Homebrew`_.

.. code-block:: shell

   brew tap adamtheturtle/literalizer-cli
   brew install literalizer-cli

.. _Homebrew: https://docs.brew.sh/Installation

With winget (Windows)
^^^^^^^^^^^^^^^^^^^^^

Requires `winget`_.

.. code-block:: shell

   winget install --id adamtheturtle.literalizer-cli --source winget --exact

The winget package may not be the latest version.

.. _winget: https://learn.microsoft.com/en-us/windows/package-manager/winget/

Pre-built Linux (x86) binaries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   $ curl --fail -L https://github.com/adamtheturtle/literalizer-cli/releases/latest/download/literalize-linux -o /usr/local/bin/literalize &&
       chmod +x /usr/local/bin/literalize

Pre-built macOS (ARM) binaries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

   $ curl --fail -L https://github.com/adamtheturtle/literalizer-cli/releases/latest/download/literalize-macos -o /usr/local/bin/literalize &&
       chmod +x /usr/local/bin/literalize

You may need to remove the quarantine attribute to run the binary:

.. code-block:: console

   $ xattr -d com.apple.quarantine /usr/local/bin/literalize

Pre-built Windows binaries
^^^^^^^^^^^^^^^^^^^^^^^^^^

Download the Windows executable from the `latest release`_ and place it in a directory on your ``PATH``.

.. _latest release: https://github.com/adamtheturtle/literalizer-cli/releases/latest

With Docker
^^^^^^^^^^^

.. code-block:: console

   $ docker run --rm -i ghcr.io/adamtheturtle/literalizer-cli:latest literalize --help

With Nix
^^^^^^^^

Requires `Nix`_.

.. code-block:: shell

   nix --extra-experimental-features 'nix-command flakes' run "github:adamtheturtle/literalizer-cli" -- --help

To avoid passing ``--extra-experimental-features`` every time, `enable flakes`_ permanently.

.. _Nix: https://nixos.org/download/
.. _enable flakes: https://wiki.nixos.org/wiki/Flakes#Enabling_flakes_permanently

Or add to your flake inputs:

.. code-block:: nix

   {
     inputs.literalizer-cli.url = "github:adamtheturtle/literalizer-cli";
   }

Usage example
-------------

.. code-block:: shell

   # Convert JSON on stdin to a Python literal
   echo '{"name": "Alice", "age": 30}' | literalize --language python

   # Convert to multiple languages
   echo '[1, 2, 3]' | literalize --language rust
   echo '{"key": "value"}' | literalize --language go

Development
-----------

.. code-block:: shell

   uv sync --extra dev
   uv run pytest

.. |Build Status| image:: https://github.com/adamtheturtle/literalizer-cli/actions/workflows/ci.yml/badge.svg?branch=main
   :target: https://github.com/adamtheturtle/literalizer-cli/actions
.. |PyPI| image:: https://badge.fury.io/py/literalizer-cli.svg
   :target: https://badge.fury.io/py/literalizer-cli
.. |minimum-python-version| replace:: 3.12
