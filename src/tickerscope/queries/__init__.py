"""GraphQL query file loader."""

from __future__ import annotations

from importlib.resources import files


def load_query(name: str) -> str:
    """Load a GraphQL query string from a .graphql file in this package.

    Args:
        name: Query file name without extension (e.g. "ownership").

    Returns:
        The raw GraphQL query string.
    """
    return files("tickerscope.queries").joinpath(f"{name}.graphql").read_text()
