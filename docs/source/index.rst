|project|
=========

CLI for literalizer - convert data structures to native language literal syntax.

.. include:: install.rst

Usage example
-------------

.. code-block:: shell

   # Convert JSON on stdin to a Python literal
   echo '{"name": "Alice", "age": 30}' | literalize --language python

   # Convert to multiple languages
   echo '[1, 2, 3]' | literalize --language rust
   echo '{"key": "value"}' | literalize --language go

Reference
---------

.. toctree::
   :maxdepth: 3

   install
   commands
   contributing
   release-process
   changelog
