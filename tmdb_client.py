import requests
import os 
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")
url = "https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc"

# fetches list of movies from api
def fetch_movie_list():
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