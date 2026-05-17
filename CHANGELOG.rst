Changelog
=========

Next
----

- Bump ``literalizer`` to 2026.5.17.
- Add ``--record-struct-name-prefix`` for naming the structs/records
  that the ``record`` ``--heterogeneous-strategy`` generates (e.g.
  ``Widget0``, ``Widget1`` instead of ``Record0``, ``Record1``).  The
  ``record`` strategy is now available for many more languages in this
  release (C, C#, C++, Crystal, D, Go, Java, Kotlin, Nim, Odin, Python,
  Rust, Scala, Swift, V, Zig); the strategy and the new option are
  surfaced automatically per language exactly like every other
  language-specific option.
- ``--heterogeneous-strategy tuple`` is now offered for the languages
  that gained the upstream ``TUPLE`` strategy (C++, Kotlin, Rust,
  Scala, TypeScript).  A tuple arity that has no native fixed-size
  tuple in the target language (e.g. a 4+-element heterogeneous array
  in Kotlin) now surfaces the new upstream
  ``TupleArityNotRepresentableError`` as a clean CLI error rather than
  a traceback.
- An invalid ``--record-struct-name-prefix`` (not a PascalCase
  identifier for the target language) now surfaces the upstream
  ``InvalidRecordNameError`` as a clean CLI error rather than a
  traceback.
- ``literalizer`` removed ``DottedCallStubNotSupportedError`` and
  ``FreeFunctionCallNotSupportedError`` (the context-aware
  ``call_transform`` made them unreachable); they are no longer
  referenced.  Languages whose declaration template previously only
  wrapped literal values (Bash, Objective-C, Tcl, and others) now bind
  a call result through their idiomatic call-binding form, so
  ``--variable-name`` in ``--mode call`` works for them too.

2026.05.14.1
------------

- Bump ``literalizer`` to 2026.5.14.1.
- YAML inputs with non-string dict keys (integers, dates, booleans)
  now flow through to the target language's value-formatting path
  instead of being silently stringified.  Languages that can represent
  the key natively (Python, Ruby, Clojure, Lua, Bash, and others)
  produce the corresponding literal; languages whose dict syntax
  requires string keys or a homogeneous typed map surface the new
  upstream ``UnrepresentableInputError`` as a clean CLI error.

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
