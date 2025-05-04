#!/usr/bin/env python3
"""
python3 birthday_reminder.py --help        # taisykles
python3 birthday_reminder.py --test        # testai
python3 birthday_reminder.py add    --user alice --name "Bob" --day 6 --month 2
python3 birthday_reminder.py list   --user alice
python3 birthday_reminder.py remind --user alice --channel console
```
"""
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



def safe_dataclass(**kwargs):  
    

    from dataclasses import dataclass as _dc  

    if sys.version_info < (3, 10):
        kwargs.pop("slots", None)
    return _dc(**kwargs)  


@safe_dataclass(frozen=True, slots=True)
class Birthday:
   
    name: str
    day: int
    month: int

    def occurs_today(self, today: date | None = None) -> bool:  
        today = today or date.today()
        return self.day == today.day and self.month == today.month


class User:
    

    def __init__(self, username: str) -> None:
        self._username: str = username
        self._birthdays: List[Birthday] = []  

    
    @property
    def username(self) -> str:  # abstraction
        return self._username

    @property
    def birthdays(self) -> tuple[Birthday, ...]:
        return tuple(self._birthdays)

   
    def add_birthday(self, birthday: Birthday) -> None:
        if any(b.name == birthday.name for b in self._birthdays):
            raise ValueError("Birthday already exists for that name.")
        self._birthdays.append(birthday)

    def remove_birthday(self, name: str) -> None:
        original_len = len(self._birthdays)
        self._birthdays = [b for b in self._birthdays if b.name != name]
        if len(self._birthdays) == original_len:
            raise ValueError("No birthday found for that name.")

    def todays_birthdays(self, today: date | None = None) -> List[Birthday]:
        today = today or date.today()
        return [b for b in self._birthdays if b.occurs_today(today)]

###########################################################################
# Persistence layer (Singleton)
###########################################################################


class _Storage:
    
    _instance: "_Storage" | None = None
    _path: Path = Path.home() / ".birthday_reminder.json"

    def __new__(cls) -> "_Storage":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._users: Dict[str, User] = {}
            cls._instance._load()
        return cls._instance

    
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

    
    def get_user(self, username: str) -> User:
        if username not in self._users:
            self._users[username] = User(username)
        return self._users[username]

    def save(self) -> None:
        self._save()


Storage = _Storage  

###########################################################################
# Notification strategies (polymorphism + Factory Method)
###########################################################################


class Notifier(ABC):
    """Abstraction that all concrete notifiers implement."""

    @abstractmethod
    def send(self, user: User, birthday: Birthday, today: date) -> None: ...


class ConsoleNotifier(Notifier):
    def send(self, user: User, birthday: Birthday, today: date) -> None:  # noqa: D401
        print(
            f"🎉  Hey {user.username}!  "
            f"Today ({today:%Y‑%m‑%d}) is {birthday.name}'s birthday!"
        )


class EmailNotifier(Notifier):
    def __init__(self, address: str) -> None:
        self._address = address

    def send(self, user: User, birthday: Birthday, today: date) -> None:  # noqa: D401
        print(
            f"[Simulated email to {self._address}] "
            f"Reminder: {birthday.name}'s birthday is today ({today:%d %b})."
        )


def _build_email_notifier_kwargs(ns: argparse.Namespace) -> Dict[str, str]:
    if ns.channel == "email" and not ns.address:
        raise SystemExit("--address is required when --channel email")
    return {"address": ns.address} if ns.address else {}


class NotifierFactory:
    @staticmethod
    def create(kind: str, **kwargs) -> Notifier:
        if kind == "console":
            return ConsoleNotifier()
        if kind == "email":
            address = kwargs.get("address")
            if not address:
                raise ValueError("Missing email address for email notifier")
            return EmailNotifier(address)
        raise ValueError(f"Unknown notifier kind: {kind}")

###########################################################################
# CLI command callbacks
###########################################################################


def _cmd_add(ns: argparse.Namespace) -> None:
    store = Storage()
    user = store.get_user(ns.user)
    user.add_birthday(Birthday(ns.name, ns.day, ns.month))
    store.save()
    print("Birthday added and saved.")


def _cmd_remove(ns: argparse.Namespace) -> None:
    store = Storage()
    user = store.get_user(ns.user)
    try:
        user.remove_birthday(ns.name)
    except ValueError as exc:
        sys.exit(str(exc))
    store.save()
    print("Birthday removed and saved.")


def _cmd_list(ns: argparse.Namespace) -> None:
    store = Storage()
    user = store.get_user(ns.user)
    if not user.birthdays:
        print("No birthdays saved.")
        return
    for bd in sorted(user.birthdays, key=lambda b: (b.month, b.day)):
        print(f"{bd.name:20} – {bd.day:02}.{bd.month:02}.")


def _cmd_remind(ns: argparse.Namespace) -> None:
    store = Storage()
    user = store.get_user(ns.user)
    notifier = NotifierFactory.create(ns.channel, **_build_email_notifier_kwargs(ns))
    todays = user.todays_birthdays()
    if not todays:
        print("No birthdays today.")
        return
    for bd in todays:
        notifier.send(user, bd, date.today())




class _TestBirthdayReminder(unittest.TestCase):
    
    def setUp(self) -> None:
        self.tmp = Path(".test_birthdays.json")
        _Storage._instance = None  
        _Storage._path = self.tmp  
        self.store = Storage()
        self.user = self.store.get_user("alice")

    def tearDown(self) -> None:
        if self.tmp.exists():
            self.tmp.unlink()

    def test_add_and_persist(self) -> None:
        self.user.add_birthday(Birthday("Bob", 6, 2))
        self.store.save()
        _Storage._instance = None
        fresh_user = Storage().get_user("alice")
        self.assertEqual(len(fresh_user.birthdays), 1)
        self.assertEqual(fresh_user.birthdays[0].name, "Bob")

    def test_cli_no_args_prints_help_and_returns_zero(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = _main([])  
        self.assertEqual(rc, 0)
        self.assertIn("usage", buf.getvalue().lower())




def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="birthday_reminder.py",
        description="Keep track of birthdays and send reminders.",
    )
    parser.add_argument("--test", action="store_true", help="Run internal unit tests and exit")

    sub = parser.add_subparsers(dest="cmd", metavar="<command>")

    # ------------------------------------------------------------------ add
    p_add = sub.add_parser("add", help="Add a birthday")
    p_add.add_argument("--user", required=True, help="Username")
    p_add.add_argument("--name", required=True, help="Person's name")
    p_add.add_argument("--day", type=int, choices=range(1, 32), required=True, help="Day 1‑31")
    p_add.add_argument("--month", type=int, choices=range(1, 13), required=True, help="Month 1‑12")
    p_add.set_defaults(func=_cmd_add)

    # ---------------------------------------------------------------- remove
    p_rm = sub.add_parser("remove", help="Remove a birthday")
    p_rm.add_argument("--user", required=True)
    p_rm.add_argument("--name", required=True)
    p_rm.set_defaults(func=_cmd_remove)

    # ------------------------------------------------------------------ list
    p_ls = sub.add_parser("list", help="List birthdays for user")
    p_ls.add_argument("--user", required=True)
    p_ls.set_defaults(func=_cmd_list)

    # --------------------------------------------------------------- remind
    p_rmd = sub.add_parser("remind", help="Remind today's birthdays")
    p_rmd.add_argument("--user", required=True)
    p_rmd.add_argument("--channel", choices=["console", "email"], default="console")
    p_rmd.add_argument("--address", help="Email address for 'email' channel")
    p_rmd.set_defaults(func=_cmd_remind)

    return parser


def _main(argv: List[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = _build_parser()

    
    if not argv:
        parser.print_help()
        return 0

    ns = parser.parse_args(argv)

    if ns.test:
        
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(_TestBirthdayReminder))
        return 0 if result.wasSuccessful() else 1

    if ns.cmd is None:  
        return 1

    
    ns.func(ns)  
    return 0


if __name__ == "__main__":  
    sys.exit(_main())
