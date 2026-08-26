Refuse empty input rather than answering differently per format. The same empty
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
