import requests
import os 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()  # By default, looks for .env in the current directory

# Get the API key
api_key = os.getenv("TMDB_API_KEY")

url = "https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc"


# initial function to return a list of movies from api
def get_movies():
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_key 
        }

    try:
        # 1. Make the request
        response = requests.get()
        
        # 2. Check if the API key or URL is valid (throws error if not 200 OK)
        response.raise_for_status()
        
        # 3. Convert raw response to a Python dictionary
        data = response.json()

        # 4. Extract just the list of movies (TMDB puts them in the 'results' key)
        return data.get('results', [])

    except requests.exceptions.RequestException as e:
        print(f"Error fetching movies: {e}")
        return [] # Return an empty list so the app doesn't crash
