"""Comandos de administración:  python -m app.cli seed | create-superadmin"""
import argparse
import getpass
import os
import sys

from app.database import get_sessionmaker
from app.modules.identity import service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed", help="Crear/actualizar permisos y roles base (idempotente)")
    sa = sub.add_parser("create-superadmin", help="Crear el primer administrador global")
    sa.add_argument("--username", required=True)
    sa.add_argument("--name", required=True)
    args = parser.parse_args(argv)

    with get_sessionmaker()() as db:
        if args.command == "seed":
            service.seed_rbac(db)
            print("Permisos y roles sincronizados.")
            return 0
        password = os.environ.get("MEMBERSHIP_ADMIN_PASSWORD")
        if not password:
            password = getpass.getpass("Contraseña (mín. 10 caracteres): ")
            if password != getpass.getpass("Repetir contraseña: "):
                print("Las contraseñas no coinciden.", file=sys.stderr)
                return 1
        user = service.create_superadmin(db, args.username, args.name, password)
        print(f"Superadmin '{user.username}' creado.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
