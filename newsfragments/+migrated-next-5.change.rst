``literalizer`` removed ``DottedCallStubNotSupportedError`` and
``FreeFunctionCallNotSupportedError`` (the context-aware
``call_transform`` made them unreachable); they are no longer
referenced.  Languages whose declaration template previously only
wrapped literal values (Bash, Objective-C, Tcl, and others) now bind
a call result through their idiomatic call-binding form, so
``--variable-name`` in ``--mode call`` works for them too.
