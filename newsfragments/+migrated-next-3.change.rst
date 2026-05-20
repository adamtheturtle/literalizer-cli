``--heterogeneous-strategy tuple`` is now offered for the languages
that gained the upstream ``TUPLE`` strategy (C++, Kotlin, Rust,
Scala, TypeScript).  A tuple arity that has no native fixed-size
tuple in the target language (e.g. a 4+-element heterogeneous array
in Kotlin) now surfaces the new upstream
``TupleArityNotRepresentableError`` as a clean CLI error rather than
a traceback.
