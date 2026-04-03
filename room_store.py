"""In-memory game rooms. Resets when the server restarts."""

import secrets
import string
import time
from typing import TypedDict


CODE_ALPHABET = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
CODE_LENGTH = 6


class Room(TypedDict):
    host_token: str
    created_at: float
    session_started: bool


rooms: dict[str, Room] = {}


def _random_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def create_room(host_token: str) -> str:
    for _ in range(100):
        code = _random_code()
        if code not in rooms:
            rooms[code] = {
                "host_token": host_token,
                "created_at": time.time(),
                "session_started": False,
            }
            return code
    raise RuntimeError("Could not allocate a room code")


def get_room(code: str) -> Room | None:
    if not code:
        return None
    return rooms.get(code.upper())


def normalize_code(code: str) -> str:
    return (code or "").strip().upper()


def mark_session_started(code: str) -> bool:
    code = normalize_code(code)
    room = rooms.get(code)
    if not room:
        return False
    room["session_started"] = True
    return True
