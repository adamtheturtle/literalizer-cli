|project|
=========

CLI for literalizer - convert data structures to native language literal syntax.

Usage example
-------------

.. code-block:: console

   $ echo '{"name": "Alice", "age": 30}' | literalize --language go
   map[string]interface{}{
       "name": "Alice",
       "age": 30,
   }

   $ echo '[1, 2, 3]' | literalize --language rust
   vec![
       1,
       2,
       3,
   ]

.. include:: install.rst

Reference
---------

.. toctree::
   :maxdepth: 3

   install
   commands
   contributing
   release-process
   changelog
