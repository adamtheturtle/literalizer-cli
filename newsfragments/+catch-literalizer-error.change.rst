Report every ``literalizer`` error as a clean CLI message. The CLI matched two
hand-maintained tuples of exception classes, so the 32 ``LiteralizerError``
subclasses missing from them escaped as Python tracebacks. Both sites now match
the ``LiteralizerError`` base class.
