Changelog
=========

.. towncrier release notes start

2026.08.29
----------

- Refuse empty input rather than answering differently per format. The same empty
  input produced a JSON parse error, ``None`` for YAML and an empty dict for TOML.

  Strip a leading byte order mark from input. It is a decoding artifact rather
  than data, and reached the parsers as content.

  Add ``--input-file`` to read input from a path instead of standard input.

  Refuse a ``--modifier`` given more than once, which previously collapsed into
  the modifier set with no feedback.

  Warn when ``--include-preamble`` is given for output that has no preamble.

  Report the ``literalizer`` version alongside the ``literalize`` version, since
  the library decides what the output looks like.

  Keep the originating library exception attached when reporting an error, rather
  than discarding it with ``from None``.

  Say in ``--help`` that language-option choices are the union across every
  language, since ``--help`` renders before ``--language`` is known.

- Reject formatting options that produce malformed output. ``--indent`` no longer
  accepts an empty string or one holding a line break, ``--ref-key`` no longer
  accepts an empty or whitespace-only marker, and ``--pre-indent-level`` is now
  bounded because each level repeats the indent on every output line.

- Reject options that the selected mode ignores. ``--call-function``,
  ``--call-params`` and ``--per-element`` in literal mode, and
  ``--pre-indent-level`` and ``--include-delimiters`` in call mode, previously
  had no effect and produced output that did not reflect the request.
  ``--no-new-variable`` without ``--variable-name`` was a silent no-op and is now
  refused too.

- Report a ``--call-params`` value that names no parameter as such. An empty,
  whitespace-only or comma-only value previously reached the arity check, which
  reported "Expected 0 parameters but got N values".

- Report every ``literalizer`` error as a clean CLI message. The CLI matched two
  hand-maintained tuples of exception classes, so the 32 ``LiteralizerError``
  subclasses missing from them escaped as Python tracebacks. Both sites now match
  the ``LiteralizerError`` base class.

- Sign the macOS binary with a Developer ID certificate and notarize it, so
  Gatekeeper no longer blocks it when it is downloaded in a browser.  The
  ``xattr -d com.apple.quarantine`` workaround is no longer needed.

2026.08.16.1
------------

No documented changes.

2026.08.16
----------

- Add manual Sphinx linkcheck and spelling pre-commit hooks to complete the lint
  tooling alignment with ``literalizer``.

- Bump ``literalizer`` to 2026.7.24.1.  The CLI now offers C++14, C++17, and
  C++20 through ``--language-version`` and exposes generated heterogeneous-value
  carrier names through ``--heterogeneous-value-variant-name``.  The release also
  adopts upstream fixes for RECORD shape inference, null-byte strings, empty
  containers, wide integers, and variable-name validation; invalid or reserved new
  variable names are surfaced as clean CLI errors.

- Expose Python annotation evaluation and union format options.

- Add ``--record-struct-name-prefix`` for naming the structs/records
  that the ``record`` ``--heterogeneous-strategy`` generates (e.g.
  ``Widget0``, ``Widget1`` instead of ``Record0``, ``Record1``).  The
  ``record`` strategy is now available for many more languages in this
  release (C, C#, C++, Crystal, D, Go, Java, Kotlin, Nim, Odin, Python,
  Rust, Scala, Swift, V, Zig); the strategy and the new option are
  surfaced automatically per language exactly like every other
  language-specific option.

- An invalid ``--record-struct-name-prefix`` (not a PascalCase
  identifier for the target language) now surfaces the upstream
  ``InvalidRecordNameError`` as a clean CLI error rather than a
  traceback.

- Bump ``literalizer`` to 2026.5.17.

- Bump ``literalizer`` to 2026.8.2.  Native multiline string formats are now
  available through ``--string-format multiline`` for supported languages, and
  ``--multiline-raw-string-delimiter-base`` configures fallback delimiters for C++
  raw strings.  Invalid C++ delimiter bases are surfaced as clean CLI errors.

- ``--heterogeneous-strategy tuple`` is now offered for the languages
  that gained the upstream ``TUPLE`` strategy (C++, Kotlin, Rust,
  Scala, TypeScript).  A tuple arity that has no native fixed-size
  tuple in the target language (e.g. a 4+-element heterogeneous array
  in Kotlin) now surfaces the new upstream
  ``TupleArityNotRepresentableError`` as a clean CLI error rather than
  a traceback.

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
