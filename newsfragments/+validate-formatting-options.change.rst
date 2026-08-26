Reject formatting options that produce malformed output. ``--indent`` no longer
accepts an empty string or one holding a line break, ``--ref-key`` no longer
accepts an empty or whitespace-only marker, and ``--pre-indent-level`` is now
bounded because each level repeats the indent on every output line.
