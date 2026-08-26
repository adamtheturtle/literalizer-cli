Refuse empty input rather than answering differently per format. The same empty
stdin produced a JSON parse error, ``None`` for YAML and an empty dict for TOML.

Refuse a ``--modifier`` given more than once, which previously collapsed into
the modifier set with no feedback.

Warn when ``--include-preamble`` is given for output that has no preamble.
