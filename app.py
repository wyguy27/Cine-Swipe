import os
import secrets
import socket
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import room_store
import tmdb_client as tmdb

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-insecure-set-FLASK_SECRET_KEY-for-production")

# queue of movies to display the users
MOVIE_QUEUE = []

# lists to store the user's liked and disliked movies
LIKED_MOVIE = []
DISLIKED_MOVIE = []

page = 1


def ensure_participant_id():
    """Stable per-browser id for attributing swipes in group sessions."""
    if not session.get("participant_id"):
        session["participant_id"] = secrets.token_urlsafe(16)


def _lan_ipv4_for_sharing() -> str | None:
    """Best-effort local IPv4 for URLs when the app is opened via localhost (QR / phones)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    return None


def _host_port_suffix(http_host: str) -> str:
    """Return ':port' from Host header, or ''. Handles [IPv6]:port and IPv4:port."""
    if http_host.startswith("["):
        end = http_host.find("]")
        if end != -1 and end + 1 < len(http_host) and http_host[end + 1] == ":":
            return http_host[end + 1 :]
        return ""
    if ":" in http_host:
        return ":" + http_host.rsplit(":", 1)[-1]
    return ""


def invite_link_abs(code: str) -> str:
    """Full /join/<code> URL for guests (QR, copy link). Uses INVITE_BASE_URL if set."""
    code = room_store.normalize_code(code)
    path = url_for("join_with_link", code=code, _external=False)
    base = (os.environ.get("INVITE_BASE_URL") or os.environ.get("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if base:
        return f"{base}{path}"
    host = (request.host or "").lower()
    if "localhost" in host or "127.0.0.1" in host or "::1" in host:
        lan = _lan_ipv4_for_sharing()
        if lan:
            port_suffix = _host_port_suffix(request.host or "")
            return f"{request.scheme}://{lan}{port_suffix}{path}"
    return url_for("join_with_link", code=code, _external=True)


def parse_host_discover_payload() -> dict[str, str]:
    """Body for POST /api/rooms: host's TMDB discover constraints for the session."""
    data = request.get_json(silent=True) or {}
    include_adult = bool(data.get("include_adult"))
    out: dict[str, str] = {
        "include_adult": "true" if include_adult else "false",
    }
    raw_ids = data.get("genre_ids") or []
    ids: list[int] = []
    for x in raw_ids:
        try:
            ids.append(int(x))
        except (TypeError, ValueError):
            continue
    if ids:
        out["with_genres"] = ",".join(str(i) for i in ids)
    lang = data.get("language")
    if isinstance(lang, str) and lang.strip() and len(lang.strip()) <= 12:
        out["with_original_language"] = lang.strip()

    rm = data.get("rating_min")
    rmx = data.get("rating_max")
    try:
        lo = float(rm) if rm is not None else None
        hi = float(rmx) if rmx is not None else None
    except (TypeError, ValueError):
        lo, hi = None, None
    if (
        lo is not None
        and hi is not None
        and 0 <= lo <= 10
        and 0 <= hi <= 10
        and lo < hi
    ):
        # TMDB discover: average vote (0–10) must fall within [lo, hi]
        out["vote_average.gte"] = str(lo)
        out["vote_average.lte"] = str(hi)

    return out


@app.route("/")
def home():
    return render_template("homepage.html")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/start")
def start():
    code = session.get("room_code")
    if code:
        code = room_store.normalize_code(code)
        room = room_store.get_room(code)
        if room is None:
            session.pop("room_code", None)
            session.pop("role", None)
            session.pop("host_token", None)
            return redirect(url_for("home"))
        if not room["session_started"]:
            return redirect(url_for("room_lobby", code=code))
    return render_template("index.html")

@app.route("/match")
def match():
    room_code = session.get("room_code")
    if not room_code:
        return redirect(url_for("home"))  # Redirect if not in a room
    
    code = room_store.normalize_code(room_code)
    room = room_store.get_room(code)
    if room is None or not room.get("session_started", False):
        return redirect(url_for("home"))  # Redirect if room invalid or swiping not started
    
    # Fetch all swipes for the room
    swipes_summary = room_store.get_all_swipes(code) or {}
    if not swipes_summary:
        return render_template("match.html", matches=[], error="No swipes yet.")
    
    # Get list of participant IDs
    participants = list(swipes_summary.keys())
    if len(participants) < 2:
        return render_template("match.html", matches=[], error="Need at least 2 participants for matches.")
    
    # Find movie IDs liked by ALL participants
    liked_by_all = set()
    for movie_id in swipes_summary[participants[0]].keys():
        if all(swipes_summary[p].get(movie_id) == "like" for p in participants):
            liked_by_all.add(movie_id)

        if not liked_by_all:
            return render_template("match.html", matches=[], error="No matches found.")
        
    # Fetch movie details for matched IDs (assuming tmdb has a fetch_movie_details function)
    matches = []
    for movie_id in liked_by_all:
        movie = tmdb.fetch_movie_details(movie_id)  # Implement this in tmdb_client if needed
        if movie:
            matches.append(movie)
    
    return render_template("match.html", matches=matches)


@app.route("/api/rooms", methods=["POST"])
def api_create_room():
    discover = parse_host_discover_payload()
    host_token = secrets.token_urlsafe(32)
    code = room_store.create_room(host_token, discover)
    session["room_code"] = code
    session["role"] = "host"
    session["host_token"] = host_token
    ensure_participant_id()
    return jsonify(
        {
            "code": code,
            "play_url": url_for("start", _external=False),
            "room_url": url_for("room_lobby", code=code, _external=False),
            "invite_url": invite_link_abs(code),
        }
    )


@app.route("/join", methods=["GET"])
def join_page():
    prefilled = request.args.get("code", "")
    err = request.args.get("error")
    return render_template("join.html", prefilled_code=prefilled, error=err)


@app.route("/join", methods=["POST"])
def join_room_submit():
    code = room_store.normalize_code(request.form.get("code", ""))
    if not code or room_store.get_room(code) is None:
        return redirect(url_for("join_page", error="invalid"))
    session["room_code"] = code
    session["role"] = "guest"
    session.pop("host_token", None)
    ensure_participant_id()
    return redirect(url_for("room_lobby", code=code))


@app.route("/join/<code>")
def join_with_link(code):
    code = room_store.normalize_code(code)
    if room_store.get_room(code) is None:
        return redirect(url_for("join_page", error="invalid"))
    session["room_code"] = code
    session["role"] = "guest"
    session.pop("host_token", None)
    ensure_participant_id()
    return redirect(url_for("room_lobby", code=code))


@app.route("/room/<code>")
def room_lobby(code):
    code = room_store.normalize_code(code)
    room = room_store.get_room(code)
    if room is None:
        return render_template("room.html", error="not_found", code=code), 404
    if session.get("room_code") != code:
        return redirect(url_for("join_page", code=code))
    ensure_participant_id()
    role = session.get("role")
    host_token = session.get("host_token")
    is_host = role == "host" and host_token == room["host_token"]
    invite_url = invite_link_abs(code)
    return render_template(
        "room.html",
        code=code,
        is_host=is_host,
        invite_url=invite_url,
    )


@app.route("/api/rooms/<code>/swiping-status")
def api_room_swiping_status(code):
    code = room_store.normalize_code(code)
    if session.get("room_code") != code:
        return jsonify({"error": "forbidden"}), 403
    room = room_store.get_room(code)
    if room is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"session_started": room["session_started"]})


@app.route("/api/rooms/<code>/start-swiping", methods=["POST"])
def api_start_swiping(code):
    code = room_store.normalize_code(code)
    room = room_store.get_room(code)
    if room is None:
        return jsonify({"error": "not_found"}), 404
    if session.get("room_code") != code:
        return jsonify({"error": "forbidden"}), 403
    role = session.get("role")
    host_token = session.get("host_token")
    if role != "host" or host_token != room["host_token"]:
        return jsonify({"error": "host_only"}), 403
    room_store.mark_session_started(code)
    return jsonify({"ok": True})


@app.route("/api/rooms/<code>/swipes")
def api_room_swipes(code):
    """All participants' like/dislike lists for this room (must be in the room)."""
    code = room_store.normalize_code(code)
    if session.get("room_code") != code:
        return jsonify({"error": "forbidden"}), 403
    if room_store.get_room(code) is None:
        return jsonify({"error": "not_found"}), 404
    ensure_participant_id()
    summary = room_store.get_all_swipes(code) or {}
    return jsonify(
        {
            "you": session["participant_id"],
            "by_participant": summary,
        }
    )


@app.route("/room/leave", methods=["POST"])
def leave_room():
    session.pop("room_code", None)
    session.pop("role", None)
    session.pop("host_token", None)
    return redirect(url_for("home"))


@app.route("/api/genres")
def get_genres():
    genres = tmdb.fetch_genres()
    return jsonify(genres)


# Gets the list of languages from the API and sends it to the frontend in JSON format
@app.route('/api/languages')
def get_languages():
    languages = tmdb.fetch_languages()
    return jsonify(languages)

# Global storage for queues, pages, and filters (in-memory, keyed by user)
movie_queues = {}
movie_pages = {}
movie_filters = {}

# Sends the next movie in the queue to the frontend in JSON format
@app.route("/api/get-next-movie")
def get_next_movie():
    room_code = session.get("room_code")
    if room_code:
        code = room_store.normalize_code(room_code)
        room = room_store.get_room(code)
        if room is None:
            return jsonify({"error": "No movies available"}), 404

        ensure_participant_id()
        user_key = f"room_{code}_{session['participant_id']}"
        filters = dict(room.get("discover_filters") or {"include_adult": "false"})
        
        if movie_filters.get(user_key) != filters:
            movie_queues[user_key] = []
            movie_pages[user_key] = 1
            movie_filters[user_key] = filters

        queue = movie_queues.get(user_key, [])
        page = movie_pages.get(user_key, 1)

        if len(queue) < 10:
            params = dict(filters)
            params["page"] = page
            batch = tmdb.fetch_movie_list(params)
            queue.extend(batch)
            page += 1
            if page > 500:
                page = 1
            movie_queues[user_key] = queue
            movie_pages[user_key] = page

        if queue:
            movie = queue.pop(0)
            movie_queues[user_key] = queue
            return jsonify(movie)
        return jsonify({"error": "No movies available"}), 404

    # For anonymous users
    if not session.get("anon_id"):
        session["anon_id"] = secrets.token_urlsafe(16)
    user_key = f"anon_{session['anon_id']}"
    
    filters = {}
    if request.args.get("isAdult") == "yes":
        filters["include_adult"] = "true"
    elif request.args.get("isAdult") == "no":
        filters["include_adult"] = "false"
    if request.args.get("genre"):
        filters["with_genres"] = request.args.get("genre")
    if request.args.get("lang"):
        filters["with_original_language"] = request.args.get("lang")

    if movie_filters.get(user_key) != filters:
        movie_queues[user_key] = []
        movie_pages[user_key] = 1
        movie_filters[user_key] = filters

    queue = movie_queues.get(user_key, [])
    page = movie_pages.get(user_key, 1)

    if len(queue) < 10:
        filters["page"] = page
        batch = tmdb.fetch_movie_list(filters)
        queue.extend(batch)
        page += 1
        if page > 500:
            page = 1
        movie_queues[user_key] = queue
        movie_pages[user_key] = page

    if queue:
        movie = queue.pop(0)
        movie_queues[user_key] = queue
        return jsonify(movie)
    return jsonify({"error": "No movies available"}), 404


if __name__ == "__main__":
    # Listen on all interfaces so phones on the same LAN can load invite URLs (QR).
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", "5000"))
    app.run(debug=True, host=host, port=port)
