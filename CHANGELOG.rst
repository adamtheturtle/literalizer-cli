Changelog
=========

Next
----

- Bump ``literalizer`` to 2026.4.21.4.
- Add ``--heterogeneous-strategy`` to pick between per-language
  strategies for collections with mixed scalar types (e.g. Rust's
  ``tagged_enum``, which emits a generated tagged ``enum`` preamble
  and wraps each value at the call site).
- Surface ``literalize_call`` errors as clean CLI messages rather
  than tracebacks: parameter-count mismatches, languages with no call
  syntax (YAML, TOML, JSON5, Norg), and languages whose call rendering
  is not yet implemented all now exit with a descriptive ``Error:``
  line.
- Add ``--modifier`` (repeatable) for declaration modifiers on new
  variables in languages that support them (Java, C#, C++).
- Remove ``--error-on-coercion``: ``literalizer`` now always errors on
  heterogeneous data that cannot be represented in the target
  language.
- Add ``--mode call`` for converting data into function call expressions,
  with ``--call-function``, ``--call-params``, and ``--per-element`` options.

2026.04.06
----------


2026.03.29
----------


- Bump ``literalizer`` to 2026.03.26.1.
- Replace ``--line-prefix`` CLI option with ``--pre-indent-level``.

2026.03.25
----------


2026.03.23.7
------------


2026.03.23.6
------------


2026.03.23.5
------------


2026.03.23.4
------------


2026.03.23.3
------------


2026.03.23.2
------------


2026.03.23.1
------------


2026.03.23
----------
