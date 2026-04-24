import os

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")


def fetch_movie_list(filters=None):
    """TMDB discover/movie. filters may include page, include_adult, with_genres, with_original_language, etc."""
    raw = dict(filters or {})
    page = raw.pop("page", 1)
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    page = max(1, min(page, 500))

    params = {
        "include_video": "false",
        "language": "en-US",
        "sort_by": "popularity.desc",
        "page": page,
    }

    inc = raw.pop("include_adult", None)
    if inc is not None:
        s = str(inc).lower()
        params["include_adult"] = "true" if s in ("true", "1", "yes") else "false"
    else:
        params["include_adult"] = "false"

    for k, v in raw.items():
        if v is None or v == "":
            continue
        params[k] = v

    url = "https://api.themoviedb.org/3/discover/movie"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key,
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        movies = data.get("results", [])

        for movie in movies:
            if movie.get("poster_path"):
                movie["poster_path"] = (
                    f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
                )

        return movies
    except Exception as e:
        print(f"Error: {e}")
        return []


def fetch_movie_details(movie_id: int) -> dict | None:
    """TMDB movie details for a single id. Returns None on failure."""
    try:
        mid = int(movie_id)
    except (TypeError, ValueError):
        return None
    url = f"https://api.themoviedb.org/3/movie/{mid}"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key,
    }
    params = {"language": "en-US"}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("poster_path"):
            data["poster_path"] = (
                f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
            )
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None


def fetch_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key,
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        genres = data.get("genres", [])
        return genres
    except Exception as e:
        print(f"Error: {e}")
        return []


def fetch_languages():
    url = "https://api.themoviedb.org/3/configuration/languages"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key,
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        languages = response.json()
        return languages
    except Exception as e:
        print(f"Error: {e}")
        return []
