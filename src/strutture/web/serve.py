"""Serve the app on one or more bind addresses (e.g. localhost + a VPN interface) with a single server."""
import ipaddress
import logging
import socket
import sys

import uvicorn
from fastapi import FastAPI

logger = logging.getLogger(__name__)
LISTEN_BACKLOG = 128


def listen_options() -> tuple[tuple[int, int, int], ...]:
    """Socket options for a listening socket. SO_REUSEADDR means "allow port sharing" on Windows,
    so there SO_EXCLUSIVEADDRUSE is used; on POSIX SO_REUSEADDR only skips the TIME_WAIT delay."""
    if sys.platform == "win32":
        return ((socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1),)
    return ((socket.SOL_SOCKET, socket.SO_REUSEADDR, 1),)


def parse_hosts(raw: str) -> tuple[str, ...]:
    """Split a comma-separated list of IP addresses, dropping duplicates but keeping order."""
    hosts = tuple(dict.fromkeys(part.strip() for part in raw.split(",") if part.strip()))
    if not hosts:
        raise ValueError("STRUTTURE_WEB_HOST is empty: give at least one bind address")
    for host in hosts:
        ipaddress.ip_address(host)  # raises ValueError on anything that is not an IP literal
    return hosts


def bind_sockets(hosts: tuple[str, ...], port: int) -> tuple[socket.socket, ...]:
    """Open one listening socket per host; if any bind fails, close the ones already opened."""
    opened: tuple[socket.socket, ...] = ()
    try:
        for host in hosts:
            family = socket.AF_INET6 if ipaddress.ip_address(host).version == 6 else socket.AF_INET
            sock = socket.socket(family, socket.SOCK_STREAM)
            opened = (*opened, sock)
            for level, option, value in listen_options():
                sock.setsockopt(level, option, value)
            sock.bind((host, port))
            sock.listen(LISTEN_BACKLOG)
    except OSError:
        for sock in opened:
            sock.close()
        logger.exception("cannot bind %s on port %s (is the VPN interface up?)", hosts, port)
        raise
    return opened


def serve(app: FastAPI, hosts: tuple[str, ...], port: int) -> None:
    sockets = bind_sockets(hosts, port)
    logger.info("serving on %s", ", ".join(f"http://{host}:{port}" for host in hosts))
    uvicorn.Server(uvicorn.Config(app)).run(sockets=list(sockets))
