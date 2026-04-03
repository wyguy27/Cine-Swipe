import requests
import os 
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")

# fetches list of movies from api
def fetch_movie_list(filters):
    url = "https://api.themoviedb.org/3/discover/movie"

    params = {
        "include_adult": "true",
        "language": "en-US",
        "sort_by": "popularity.desc"
    }

    params.update(filters)

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        movies = data.get('results', [])
        
        # Add full image paths now so the frontend doesn't have to
        for movie in movies:
            if movie.get('poster_path'):
                movie['poster_path'] = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        
        return movies
    except Exception as e:
        print(f"Error: {e}")
        return []
    
# fetches list of genres from api
def fetch_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        genres = data.get('genres', [])
        return genres
    except Exception as e:
        print(f"Error: {e}")
        return []
    

# fetches list of languages from api
def fetch_languages():
    url = "https://api.themoviedb.org/3/configuration/languages"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        languages = response.json()
        return languages
    except Exception as e:
        print(f"Error: {e}")
        return []