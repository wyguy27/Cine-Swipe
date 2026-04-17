"""In-memory game rooms. Resets when the server restarts."""

import secrets
import string
import time
from typing import Any, TypedDict


CODE_ALPHABET = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
CODE_LENGTH = 6


class Room(TypedDict, total=False):
    host_token: str
    created_at: float
    session_started: bool
    member_swipes: dict[str, dict[str, list[int]]]
    discover_filters: dict[str, str]
    movie_queue: list
    discover_page: int


rooms: dict[str, Room] = {}


def _random_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def create_room(host_token: str, discover_filters: dict[str, str] | None = None) -> str:
    base_filters = discover_filters or {"include_adult": "false"}
    for _ in range(100):
        code = _random_code()
        if code not in rooms:
            rooms[code] = {
                "host_token": host_token,
                "created_at": time.time(),
                "session_started": False,
                "member_swipes": {},
                "discover_filters": dict(base_filters),
                "movie_queue": [],
                "discover_page": 1,
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


def _norm_movie_id(movie_id: Any) -> int | None:
    if movie_id is None:
        return None
    try:
        return int(movie_id)
    except (TypeError, ValueError):
        return None


def record_swipe(code: str, participant_id: str, movie_id: Any, vote: str) -> bool:
    """Record one swipe for a participant in a room. vote is \"like\" or \"dislike\"."""
    code = normalize_code(code)
    room = rooms.get(code)
    if not room or not participant_id:
        return False
    mid = _norm_movie_id(movie_id)
    if mid is None or vote not in ("like", "dislike"):
        return False
    ms = room.setdefault("member_swipes", {})
    if participant_id not in ms:
        ms[participant_id] = {"likes": [], "dislikes": []}
    bucket = ms[participant_id]
    if mid in bucket["likes"]:
        bucket["likes"].remove(mid)
    if mid in bucket["dislikes"]:
        bucket["dislikes"].remove(mid)
    if vote == "like":
        bucket["likes"].append(mid)
    else:
        bucket["dislikes"].append(mid)
    return True


def get_participant_swipes(code: str, participant_id: str) -> dict[str, list[int]] | None:
    code = normalize_code(code)
    room = rooms.get(code)
    if not room or not participant_id:
        return None
    ms = room.get("member_swipes") or {}
    bucket = ms.get(participant_id)
    if not bucket:
        return {"likes": [], "dislikes": []}
    return {
        "likes": list(bucket.get("likes", [])),
        "dislikes": list(bucket.get("dislikes", [])),
    }


def get_all_swipes(code: str) -> dict[str, dict[str, list[int]]] | None:
    """participant_id -> {\"likes\": [...], \"dislikes\": [...]}"""
    code = normalize_code(code)
    room = rooms.get(code)
    if not room:
        return None
    ms = room.get("member_swipes") or {}
    out: dict[str, dict[str, list[int]]] = {}
    for pid, bucket in ms.items():
        out[pid] = {
            "likes": list(bucket.get("likes", [])),
            "dislikes": list(bucket.get("dislikes", [])),
        }
    return out


def add_swipe(code: str, participant_id: str, movie_id: int, action: str):
    """Record a like/dislike for a participant in the room."""
    room = rooms.get(code)
    if room:
        swipes = room.setdefault("swipes", {})
        participant_swipes = swipes.setdefault(participant_id, {})
        participant_swipes[movie_id] = action

def get_all_swipes(code: str) -> dict:
    """Return all swipes: {participant_id: {movie_id: 'like'/'dislike'}}"""
    room = rooms.get(code)
    if room:
        return room.get("swipes", {})
    return {}