"""Command-line tooling for the local GXP reference demonstrator."""

from __future__ import annotations

import argparse
import json
import sys

from .ingestion import IngestionStore
from .server import serve


def _server_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", required=True, help="SQLite database path")
    parser.add_argument("--host", default="127.0.0.1", help="Development binding; loopback is the safe default")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--certfile", help="TLS certificate PEM")
    parser.add_argument("--keyfile", help="TLS private key PEM")
    parser.add_argument("--client-ca-file", help="Optional client CA PEM; requires a client TLS certificate")


def _bootstrap_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--db", required=True, help="SQLite database path")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--replace", action="store_true", help="Rotate an existing development token")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Experimental GXP reference tooling")
    subcommands = result.add_subparsers(dest="command", required=True)
    _server_parser(subcommands.add_parser("server", help="Run a local ingestion server"))
    _bootstrap_parser(subcommands.add_parser("bootstrap-device", help="Create or rotate a device development token"))
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    store = IngestionStore(args.db)
    if args.command == "bootstrap-device":
        try:
            token = store.bootstrap_device(args.tenant, args.device, replace=args.replace)
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 2
        print(json.dumps({"tenant": args.tenant, "device": args.device, "token": token, "warning": "Store this token now; it is not retrievable later."}))
        return 0
    serve(
        store,
        host=args.host,
        port=args.port,
        certfile=args.certfile,
        keyfile=args.keyfile,
        client_ca_file=args.client_ca_file,
    )
    return 0


def server_main() -> int:
    return main(["server", *sys.argv[1:]])


def bootstrap_device_main() -> int:
    return main(["bootstrap-device", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())

