"""Domain errors the CLI can map to a message and an exit code."""

from __future__ import annotations


class UsageError(ValueError):
    """Invalid input. The CLI exits 2."""


class InvalidIdentifierError(UsageError):
    """Identifier failed the strict id grammar. The CLI exits 2."""


class PathEscapeError(UsageError):
    """A resolved artifact path left ``.retornatus``. The CLI exits 2."""


class SigningKeyError(UsageError):
    """Private signing key is missing or malformed. The CLI exits 2."""


class SearchQueryError(UsageError):
    """A search query could not be executed. The CLI exits 2."""


class ReceiptError(UsageError):
    """A receipt file is not usable. The CLI exits 2."""
