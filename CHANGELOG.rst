Changelog
=========

Next
----

2026.05.14
----------

- Bump ``literalizer`` to 2026.5.14.
- ``--variable-name`` (with ``--new-variable`` / ``--no-new-variable``
  and ``--modifier``) now applies in ``--mode call`` as well, wrapping
  the rendered call in the language's idiomatic per-language variable
  binding (e.g. ``let user = createUser(...)``,
  ``const user = createUser(...)``,
  ``user = create_user(...)``).  Mutability and inference are picked
  up from ``--declaration-style`` and ``--modifier`` exactly as in
  literal mode.  Languages whose declaration template wraps or
  transforms the right-hand side in a way only valid for literal
  values (e.g. Bash command substitution, Objective-C boxing,
  tagged-enum heterogeneous-strategy languages) surface the upstream
  ``UnsupportedCallShapeError`` as a clean CLI error, as does the
  combination with ``--per-element`` (which has no per-element name
  vector).

2026.05.13
----------

- Bump ``literalizer`` to 2026.5.13.1.  The new release re-exposes the
  ``supports_*`` class attributes for ``empty_dict_key``, ``call_style``,
  and the five ``default_*_type`` options, restoring a type-safe probe
  for runtime-dispatched constructor kwargs (cf. upstream issue
  #2147).
- Replace ``--line-ending`` with ``--statement-terminator-style``.  The
  upstream ``LineEndings`` enum was removed; ``StatementTerminatorStyles``
  (``semicolon``, ``none``) is its successor.
- Add ``--call-style`` for picking between per-language call shapes
  (e.g. ``curried`` for Haskell / OCaml / F# / SML / Elm, ``named`` for
  Visual Basic).
- Add ``--numeric-style`` for languages that support multiple numeric
  rendering styles (e.g. ``overloaded`` vs. ``explicit``).
- Add ``--language-version`` for selecting the target language version
  (each language exposes a ``VersionFormats`` enum).
- Add ``--module-name`` for languages whose ``--wrap-in-file`` form
  introduces a named scope (C, C++, D, Erlang, Fortran, F#, Java,
  Objective-C, Occam, SystemVerilog).  Previously a ``module_name``
  argument to ``literalize`` itself, now a per-language constructor
  argument.
- Add ``--ref-key`` for picking a marker key other than ``$ref`` for
  variable-reference mappings in the input data.
- Surface the new typed ``literalizer`` exceptions as clean CLI errors
  rather than tracebacks: ``UnsupportedCallShapeError``,
  ``VariableNameNotSupportedError``,
  ``WrapInFileWithoutVariableNotSupportedError``,
  ``WrapCombinedInFileNotSupportedError``,
  ``DottedCallTargetNotSupportedError``,
  ``DottedCallStubNotSupportedError``,
  ``FreeFunctionCallNotSupportedError``,
  ``CallArgNotSupportedError``,
  ``HeterogeneousScalarCollectionError``,
  ``UnrepresentableSpecialFloatError``.
- ``--variable-type-hints auto`` is now ``--variable-type-hints never``
  (upstream rename), with a new ``safe`` option that annotates only
  when the language's own inference would widen the variable to a
  permissive type (e.g. ``unknown[]`` for an empty TypeScript array).

2026.04.30
----------


- Bump ``literalizer`` to 2026.4.29 (adds Roc, Wren, Mojo, V, Ada, Nim,
  Tcl, Scheme, PureScript, OCaml, SystemVerilog, COBOL, Fortran, Dart,
  Dhall, Elixir, Elm, and PowerShell to ``literalize_call`` support).
- Add ``--ref-case`` for emitting ``$ref`` markers in input data as
  bare identifiers re-cased to ``snake``, ``camel``, ``pascal``,
  ``upper_snake``, or ``kebab``.
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
