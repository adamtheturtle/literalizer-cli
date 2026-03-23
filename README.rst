literalizer-cli
================

CLI for literalizer - convert data structures to native language literal syntax.

Installation
------------

pip
~~~

Requires Python 3.11+.

.. code-block:: shell

   pip install literalizer-cli

Homebrew (macOS/Linux)
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

   brew tap adamtheturtle/literalizer-cli
   brew install literalizer-cli

Pre-built binaries
~~~~~~~~~~~~~~~~~~

Download the latest binary for your platform from the
`GitHub releases page <https://github.com/adamtheturtle/literalizer-cli/releases/latest>`__.

Linux:

.. code-block:: shell

   curl -L https://github.com/adamtheturtle/literalizer-cli/releases/download/2026.03.23/literalize-linux -o literalize
   chmod +x literalize

Docker
~~~~~~

.. code-block:: shell

   docker run --rm -i ghcr.io/adamtheturtle/literalizer-cli:latest literalize

Nix
~~~

.. code-block:: shell

   nix run github:adamtheturtle/literalizer-cli/2026.03.23

winget (Windows)
~~~~~~~~~~~~~~~~

.. code-block:: shell

   winget install adamtheturtle.literalizer-cli

Development
-----------

.. code-block:: shell

   $ uv sync --extra dev
   $ uv run pytest
