Reject options that the selected mode ignores. ``--call-function``,
``--call-params`` and ``--per-element`` in literal mode, and
``--pre-indent-level`` and ``--include-delimiters`` in call mode, previously
had no effect and produced output that did not reflect the request.
``--no-new-variable`` without ``--variable-name`` was a silent no-op and is now
refused too.
