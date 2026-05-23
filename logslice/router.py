"""Route log entries to different sinks based on field values or patterns.

Provides a flexible routing layer that dispatches LogEntry objects to one
or more named output queues depending on configurable rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from logslice.parser import LogEntry

# A predicate takes a LogEntry and returns True if the entry matches the route.
RoutePredicate = Callable[[LogEntry], bool]


@dataclass
class Route:
    """A single named route with an associated predicate."""

    name: str
    predicate: RoutePredicate


@dataclass
class RoutedEntry:
    """An entry paired with the name of the route it was dispatched to."""

    route: str
    entry: LogEntry


@dataclass
class Router:
    """Holds an ordered list of routes and a fallback sink name.

    Entries are evaluated against routes in order.  The first matching route
    wins.  If no route matches, the entry is sent to *fallback* (default:
    ``"default"``).
    """

    routes: List[Route] = field(default_factory=list)
    fallback: str = "default"

    def add_route(self, name: str, predicate: RoutePredicate) -> "Router":
        """Append a route and return *self* for chaining."""
        self.routes.append(Route(name=name, predicate=predicate))
        return self


def make_level_route(name: str, level: str) -> Route:
    """Return a Route that matches entries whose level equals *level* (case-insensitive)."""
    _level = level.upper()

    def _pred(entry: LogEntry) -> bool:
        return (entry.level or "").upper() == _level

    return Route(name=name, predicate=_pred)


def make_pattern_route(name: str, pattern: str) -> Route:
    """Return a Route that matches entries whose message contains *pattern* (regex)."""
    _re = re.compile(pattern)

    def _pred(entry: LogEntry) -> bool:
        return bool(_re.search(entry.message or ""))

    return Route(name=name, predicate=_pred)


def make_field_route(name: str, field_name: str, value: str) -> Route:
    """Return a Route that matches entries where *extra[field_name]* equals *value*."""

    def _pred(entry: LogEntry) -> bool:
        extra = entry.extra or {}
        return str(extra.get(field_name, "")) == value

    return Route(name=name, predicate=_pred)


def route_entry(router: Router, entry: LogEntry) -> str:
    """Return the name of the first matching route for *entry*, or the fallback."""
    for route in router.routes:
        if route.predicate(entry):
            return route.name
    return router.fallback


def route_entries(
    router: Router,
    entries: Iterable[LogEntry],
) -> Iterator[RoutedEntry]:
    """Yield :class:`RoutedEntry` objects for every entry in *entries*."""
    for entry in entries:
        yield RoutedEntry(route=route_entry(router, entry), entry=entry)


def split_by_route(
    router: Router,
    entries: Iterable[LogEntry],
) -> Dict[str, List[LogEntry]]:
    """Consume *entries* and return a dict mapping route name → list of entries.

    All route names (including the fallback) that receive at least one entry
    are present as keys.  Routes that match nothing are omitted.
    """
    buckets: Dict[str, List[LogEntry]] = {}
    for routed in route_entries(router, entries):
        buckets.setdefault(routed.route, []).append(routed.entry)
    return buckets
