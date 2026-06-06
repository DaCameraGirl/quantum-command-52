from __future__ import annotations

import argparse
from typing import Iterable

from server import db_cursor, init_db, init_pool, load_dotenv_file, seed_user_transactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed the real estate transaction pipeline board for dashboard users.",
    )
    parser.add_argument(
        "--email",
        help="Seed only the user with this email address. Defaults to every registered user.",
    )
    return parser.parse_args()


def load_target_users(email: str | None) -> Iterable[dict]:
    with db_cursor() as cursor:
        if email:
            cursor.execute(
                "SELECT id, email, display_name FROM user_profiles WHERE email = %s",
                (email.strip().lower(),),
            )
        else:
            cursor.execute("SELECT id, email, display_name FROM user_profiles ORDER BY id")
        return cursor.fetchall()


def main() -> None:
    args = parse_args()
    load_dotenv_file()
    init_pool()
    init_db()

    users = list(load_target_users(args.email))
    if not users:
        if args.email:
            print(f"No dashboard user found for {args.email}. Register that user first.")
        else:
            print("No dashboard users found. Register at least one user before seeding transactions.")
        return

    with db_cursor(commit=True) as cursor:
        for user in users:
            seed_user_transactions(cursor, int(user["id"]))
            print(f"Seeded transaction board for {user['email']} ({user['display_name']}).")


if __name__ == "__main__":
    main()
