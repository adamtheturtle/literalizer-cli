Installation
------------

With ``pip``
~~~~~~~~~~~~

Requires Python |minimum-python-version|\+.

.. code-block:: console

   $ pip install literalizer-cli

With Homebrew (macOS, Linux, WSL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Requires `Homebrew`_.

.. code-block:: console

   $ brew tap adamtheturtle/literalizer-cli
   $ brew install literalizer-cli

.. _Homebrew: https://docs.brew.sh/Installation

With winget (Windows)
~~~~~~~~~~~~~~~~~~~~~

Requires `winget`_.

.. code-block:: console

   $ winget install --id adamtheturtle.literalizer-cli --source winget --exact

The winget package may not be the latest version.

.. _winget: https://learn.microsoft.com/en-us/windows/package-manager/winget/

Pre-built Linux (x86) binaries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console
   :substitutions:

   $ curl --fail -L "https://github.com/|github-owner|/|github-repository|/releases/download/|release|/literalize-linux" -o /usr/local/bin/literalize &&
       chmod +x /usr/local/bin/literalize

Pre-built macOS (ARM) binaries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console
   :substitutions:

   $ curl --fail -L "https://github.com/|github-owner|/|github-repository|/releases/download/|release|/literalize-macos" -o /usr/local/bin/literalize &&
       chmod +x /usr/local/bin/literalize

You may need to remove the quarantine attribute to run the binary:

.. code-block:: console

   $ xattr -d com.apple.quarantine /usr/local/bin/literalize

Pre-built Windows binaries
~~~~~~~~~~~~~~~~~~~~~~~~~~

Download the Windows executable from the `latest release`_ and place it in a directory on your ``PATH``.

.. _latest release: https://github.com/adamtheturtle/literalizer-cli/releases/latest

With Docker
~~~~~~~~~~~

.. code-block:: console
   :substitutions:

   $ docker run --rm -i "|docker-image|" literalize --help

With Nix
~~~~~~~~

Requires `Nix`_.

.. code-block:: console
   :substitutions:

   $ nix --extra-experimental-features 'nix-command flakes' run "github:|github-owner|/|github-repository|/|release|" -- --help

To avoid passing ``--extra-experimental-features`` every time, `enable flakes`_ permanently.

.. _Nix: https://nixos.org/download/
.. _enable flakes: https://wiki.nixos.org/wiki/Flakes#Enabling_flakes_permanently

Or add to your flake inputs:

.. code-block:: nix

   {
     inputs.literalizer-cli.url = "github:adamtheturtle/literalizer-cli";
   }
