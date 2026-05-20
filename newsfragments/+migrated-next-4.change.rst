An invalid ``--record-struct-name-prefix`` (not a PascalCase
identifier for the target language) now surfaces the upstream
``InvalidRecordNameError`` as a clean CLI error rather than a
traceback.
