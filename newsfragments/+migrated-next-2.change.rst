Add ``--record-struct-name-prefix`` for naming the structs/records
that the ``record`` ``--heterogeneous-strategy`` generates (e.g.
``Widget0``, ``Widget1`` instead of ``Record0``, ``Record1``).  The
``record`` strategy is now available for many more languages in this
release (C, C#, C++, Crystal, D, Go, Java, Kotlin, Nim, Odin, Python,
Rust, Scala, Swift, V, Zig); the strategy and the new option are
surfaced automatically per language exactly like every other
language-specific option.
