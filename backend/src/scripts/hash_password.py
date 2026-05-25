"""Interactive CLI to generate a bcrypt hash for ADMIN_PASSWORD_HASH / SYSTEM_PASSWORD_HASH.

Usage:
    docker compose exec backend python -m src.scripts.hash_password
    # OR locally (with bcrypt installed):
    python -m src.scripts.hash_password
"""

from __future__ import annotations

import getpass
import sys

from src.core.security import hash_password


def main() -> int:
    print("Generate a bcrypt hash for backend/.env")
    print("---------------------------------------")
    pwd = getpass.getpass("Password: ")
    if not pwd:
        print("ERROR: empty password.", file=sys.stderr)
        return 1
    confirm = getpass.getpass("Confirm:  ")
    if pwd != confirm:
        print("ERROR: passwords do not match.", file=sys.stderr)
        return 1
    print()
    print("Bcrypt hash (paste into ADMIN_PASSWORD_HASH or SYSTEM_PASSWORD_HASH):")
    print(hash_password(pwd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
