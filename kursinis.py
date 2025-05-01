#!/usr/bin/env python3


from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import unittest
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List

###########################################################################
# Domain layer                                                             
###########################################################################


@dataclass(frozen=True, slots=True)
class Birthday:
    """Immutable value object representing a single birthday."""

    name: str
    day: int
    month: int

    def occurs_today(self, today: date | None = None) -> bool:
        """Return *True* if this birthday is today (defaults to today’s date)."""
        today = today or date.today()
        return self.day == today.day and self.month == today.month


class User:
    """A system user who *owns* an arbitrary number of :class:`Birthday`s.

    **Encapsulation** – the internal ``_birthdays`` list is private; callers
    interact only through the public methods.  The class demonstrates
    **composition** because a *User has‑a collection of Birthday objects*.
    """

    def __init__(self, username: str) -> None:
        self._username: str = username
        self._birthdays: List[Birthday] = []

    # -------------------------- read‑only views ------------------------- #
    @property
    def username(self) -> str:  # abstraction: hide field name
        return self._username

    @property
    def birthdays(self) -> tuple[Birthday, ...]:  # immutable proxy
        return tuple(self._birthdays)

    # ----------------------------- behaviour --------------------------- #
    def add_birthday(self, birthday: Birthday) -> None:
        if any(b.name == birthday.name for b in self._birthdays):
            raise ValueError("Birthday already exists for that name.")
        self._birthdays.append(birthday)

    def remove_birthday(self, name: str) -> None:
        self._birthdays = [b for b in self._birthdays if b.name != name]

    # Helper for reminder logic
    def todays_birthdays(self, today: date | None = None) -> List[Birthday]:
        today = today or date.today()
        return [b for b in self._birthdays if b.occurs_today(today)]


###########################################################################
# Persistence layer (Singleton)                                            
###########################################################################


class _Storage:
    """JSON–backed persistence implemented as a **Singleton**.

    The first call to ``Storage()`` creates the instance; subsequent calls
    return the same object.  Public API: :meth:`get_user` and :meth:`save`.
    """

    _instance: "_Storage" | None = None
    _path: Path = Path.home() / ".birthday_reminder.json"

    def __new__(cls) -> "_Storage":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._users: Dict[str, User] = {}
            cls._instance._load()
        return cls._instance

    # -------------------------- private helpers ------------------------ #
    def _load(self) -> None:
        if self._path.exists():
            with self._path.open(encoding="utf‑8") as fp:
                raw = json.load(fp)
            for username, recs in raw.items():
                user = User(username)
                for rec in recs:
                    user.add_birthday(Birthday(**rec))
                self._users[username] = user

    def _save(self) -> None:
        data = {
            u.username: [
                {"name": b.name, "day": b.day, "month": b.month}
                for b in u.birthdays
            ]
            for u in self._users.values()
        }
        with self._path.open("w", encoding="utf‑8") as fp:
            json.dump(data, fp, indent=2)

    # ---------------------------- public API --------------------------- #
    def get_user(self, username: str) -> User:
        if username not in self._users:
            self._users[username] = User(username)
        return self._users[username]

    def save(self) -> None:
        self._save()


# Alias used by the rest of the module – hides the underscore from users
Storage = _Storage  # type: ignore[var‑annotated]

###########################################################################
# Notification strategies (polymorphism + Factory Method)                  
###########################################################################


class Notifier(ABC):
    """Abstraction that all concrete notifiers must implement."""

    @abstractmethod
    def send(self, user: User, birthday: Birthday, today: date) -> None:  # noqa: D401
        """Send a reminder – to be implemented by subclasses."""


class ConsoleNotifier(Notifier):
    """Default notifier: prints a message to *stdout*."""

    def send(self, user: User, birthday: Birthday, today: date) -> None:  # noqa: D401
        print(
            f"\N{PARTY POPPER}  Hey {user.username}!  "
            f"Today ({today:%Y‑%m‑%d}) is {birthday.name}'s birthday!"
        )


class EmailNotifier(Notifier):
    """Placeholder email notifier (simulated)."""

    def __init__(self, address: str) -> None:  # encapsulation of state
        self._address = address

    def send(self, user: User, birthday: Birthday, today: date) -> None:  # noqa: D401
        print(
            f"[Simulated email to {self._address}] "
            f"Reminder: {birthday.name}'s birthday is today ({today:%d %b})!"
        )


class NotifierFactory:
    """**Factory‑Method** pattern to obtain a concrete :class:`Notifier`."""

    @staticmethod
    def create(kind: str, **kwargs) -> Notifier:
        if kind == "console":
            return ConsoleNotifier()
        if kind == "email":
            try:
                return EmailNotifier(kwargs["address"])
            except KeyError as exc:  # pragma: no cover – config error
                raise ValueError("'address' parameter missing for email notifier") from exc
        raise ValueError(f"Unknown notifier kind: {kind}")

###########################################################################
# Application layer – simple CLI                                           
###########################################################################


def _cmd_add(args: argparse.Namespace) -> None:
    store = Storage()
    user = store.get_user(args.user)
    user.add_birthday(Birthday(args.name, args.day, args.month))
    store.save()
    print("Birthday added and saved.")


def _cmd_remove(args: argparse.Namespace) -> None:
    store = Storage()
    user = store.get_user(args.user)
    user.remove_birthday(args.name)
    store.save()
    print("Birthday removed and saved.")


def _cmd_list(args: argparse.Namespace) -> None:
    store = Storage()
    user = store.get_user(args.user)
    if not user.birthdays:
        print("No birthdays saved.")
        return
    for bd in sorted(user.birthdays, key=lambda b: (b.month, b.day)):
        print(f"{bd.name:20} – {bd.day:02}.{bd.month:02}.")


def _cmd_remind(args: argparse.Namespace) -> None:
    store = Storage()
    user = store.get_user(args.user)
    today = date.today()
    notifier = NotifierFactory.create(args.channel, address=args.address)
    todays = user.todays_birthdays(today)
    if not todays:
        print("No birthdays today.")
        return
    for bd in todays:
        notifier.send(user, bd, today)


###########################################################################
# Unit tests                                                               
###########################################################################


class _TestBirthdayReminder(unittest.TestCase):
    """Happy‑path + edge‑case test‑suite covering the core use‑cases."""

    def setUp(self) -> None:  # runs before each test
        # Use an in‑memory *temporary* storage path
        self._tmp_path = Path(".test_birthdays.json")
        _Storage._instance = None  # force new singleton
        _Storage._path = self._tmp_path  # type: ignore[attr‑defined]
        self.store = Storage()
        self.user = self.store.get_user("alice")

    def tearDown(self) -> None:  # clean up
        if self._tmp_path.exists():
            self._tmp_path.unlink()

    # -------------------------- tests ---------------------------------- #
    def test_add_and_persist_birthday(self) -> None:
        self.user.add

