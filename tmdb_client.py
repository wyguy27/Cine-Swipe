import requests
import os 
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")

# Base url that will be used for all types of movie searches
search_url = "https://api.themoviedb.org/3/discover/movie"

# fetches list of movies from api
def fetch_movie_list():
    url = "https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key 
    }
    try:
        response = requests.get(url, headers=headers)
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
    

# fetch runtime of a movie by movie id
def fetch_movie_runtime(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key
    }   

    try: 
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get('runtime', None)
    
    except Exception as e: 
        print(f"Error fetching runtime: {e}")
        return None