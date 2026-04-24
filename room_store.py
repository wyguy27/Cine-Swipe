"""In-memory game rooms. Resets when the server restarts."""

import secrets
import string
import time


CODE_ALPHABET = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
CODE_LENGTH = 6

MAX_PARTICIPANTS_DEFAULT = 2

rooms: dict[str, dict] = {}


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
                "discover_filters": dict(base_filters),
                "movie_queue": [],
                "discover_page": 1,
                "swiping_participants": set(),
                "participants": set(),
                "max_participants": MAX_PARTICIPANTS_DEFAULT,
                "winner_movie_id": None,
                "swipes": {},
            }
            return code
    raise RuntimeError("Could not allocate a room code")


def get_room(code: str) -> dict | None:
    if not code:
        return None
    return rooms.get(code.upper())


def normalize_code(code: str) -> str:
    return (code or "").strip().upper()

def can_join_room(code: str) -> bool:
    code = normalize_code(code)
    room = rooms.get(code)
    if not room:
        return False
    return len(room.get("participants", set())) < room.get("max_participants", 0)

def add_participant(code: str, participant_id: str) -> bool:
    code = normalize_code(code)
    room = rooms.get(code)
    if not room or not participant_id:
        return False
    
    participants = room.setdefault("participants", set())
    max_participants = room.get("max_participants", 0)
    if len(participants) >= max_participants:
        return False
    
    participants.add(participant_id)
    return True

def remove_participant(code: str, participant_id: str) -> None:
    code = normalize_code(code)
    room = rooms.get(code)
    if room and participant_id:
        room.setdefault("participants", set()).discard(participant_id)

def get_participant_count(code: str) -> int:
    code = normalize_code(code)
    room = rooms.get(code)
    return len(room.get("participants", set())) if room else 0


def mark_session_started(code: str) -> bool:
    code = normalize_code(code)
    room = rooms.get(code)
    if not room:
        return False
    room["session_started"] = True
    return True


def register_swiping_participant(code: str, participant_id: str) -> None:
    """Anyone who loads the swipe feed is counted for group consensus."""
    code = normalize_code(code)
    room = rooms.get(code)
    if room and participant_id:
        room.setdefault("swiping_participants", set()).add(participant_id)


def add_swipe(code: str, participant_id: str, movie_id: int, action: str) -> None:
    code = normalize_code(code)
    room = rooms.get(code)
    if room:
        swipes = room.setdefault("swipes", {})
        participant_swipes = swipes.setdefault(participant_id, {})
        participant_swipes[movie_id] = action


def get_all_swipes(code: str) -> dict:
    code = normalize_code(code)
    room = rooms.get(code)
    if room:
        return dict(room.get("swipes") or {})
    return {}


def maybe_set_winner_from_swipes(code: str) -> int | None:
    """
    If at least two swiping participants all have 'like' on the same movie, set winner_movie_id once.
    Returns the winning movie id if set or already stored, else None.
    """
    code = normalize_code(code)
    room = rooms.get(code)
    if not room:
        return None
    existing = room.get("winner_movie_id")
    if existing is not None:
        return int(existing)

    participants = room.get("swiping_participants") or set()
    if len(participants) < 2:
        return None

    swipes = room.get("swipes") or {}
    p_list = sorted(participants)
    anchor = p_list[0]
    for mid, action in swipes.get(anchor, {}).items():
        if action != "like":
            continue
        if all(swipes.get(p, {}).get(mid) == "like" for p in p_list):
            room["winner_movie_id"] = int(mid)
            return int(mid)
    return None


def get_winner_movie_id(code: str) -> int | None:
    code = normalize_code(code)
    room = rooms.get(code)
    if not room:
        return None
    wid = room.get("winner_movie_id")
    return int(wid) if wid is not None else None


def clear_winner(code: str) -> None:
    code = normalize_code(code)
    room = rooms.get(code)
    if room:
        winner_id = room.get("winner_movie_id")
        if winner_id is not None:
            swipes = room.get("swipes", {})
            for participant_swipes in swipes.values():
                participant_swipes.pop(int(winner_id), None)
        room["winner_movie_id"] = None