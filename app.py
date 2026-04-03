import os
import secrets
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

@app.route("/")
def home():
    return render_template("homepage.html")


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


@app.route("/api/rooms", methods=["POST"])
def api_create_room():
    host_token = secrets.token_urlsafe(32)
    code = room_store.create_room(host_token)
    session["room_code"] = code
    session["role"] = "host"
    session["host_token"] = host_token
    return jsonify(
        {
            "code": code,
            "play_url": url_for("start", _external=False),
            "room_url": url_for("room_lobby", code=code, _external=False),
            "invite_url": url_for("join_with_link", code=code, _external=True),
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
    return redirect(url_for("room_lobby", code=code))


@app.route("/join/<code>")
def join_with_link(code):
    code = room_store.normalize_code(code)
    if room_store.get_room(code) is None:
        return redirect(url_for("join_page", error="invalid"))
    session["room_code"] = code
    session["role"] = "guest"
    session.pop("host_token", None)
    return redirect(url_for("room_lobby", code=code))


@app.route("/room/<code>")
def room_lobby(code):
    code = room_store.normalize_code(code)
    room = room_store.get_room(code)
    if room is None:
        return render_template("room.html", error="not_found", code=code), 404
    if session.get("room_code") != code:
        return redirect(url_for("join_page", code=code))
    role = session.get("role")
    host_token = session.get("host_token")
    is_host = role == "host" and host_token == room["host_token"]
    invite_url = url_for("join_with_link", code=code, _external=True)
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

# Sends the next movie in the queue to the frontend in JSON format
@app.route('/api/get-next-movie')
def get_next_movie():
    global MOVIE_QUEUE, page
    
    filters = {
                    "include_adult": request.args.get('isAdult'),
                    "with_genres": request.args.get('genre'),
                    "with_language": request.args.get('lang'),
                    "page": page
                }

    if not MOVIE_QUEUE:
        print("Queue empty! Fetching new movies from TMDB...")
        MOVIE_QUEUE = tmdb.fetch_movie_list(filters)
        page += 1
        if page > 500:
            page = 1

    if MOVIE_QUEUE:
        single_movie = MOVIE_QUEUE.pop(0)
        return jsonify(single_movie)

    return jsonify({"error": "No movies available"}), 404


@app.route("/api/vote", methods=["POST"])
def handle_vote():
    data = request.json
    movie_id = data.get("id")
    vote_type = data.get("vote")

    if vote_type == "like":
        LIKED_MOVIE.append(movie_id)
    elif vote_type == "dislike":
        DISLIKED_MOVIE.append(movie_id)

    return jsonify(
        {
            "message": "Vote received",
            "liked_movies": LIKED_MOVIE,
            "disliked_movies": DISLIKED_MOVIE,
        }
    )




if __name__ == '__main__':
    app.run(debug=True)
