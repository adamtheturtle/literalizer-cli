Report the ``literalizer`` version alongside the ``literalize`` version, since
the library decides what the output looks like.

Keep the originating library exception attached when reporting an error, rather
than discarding it with ``from None``.
