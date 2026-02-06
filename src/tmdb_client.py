import requests
import os 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()  # By default, looks for .env in the current directory

# Get the API key
api_key = os.getenv("TMDB_API_KEY")

url = "https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=false&language=en-US&page=1&sort_by=popularity.desc"

headers = {
    "accept": "application/json",
    "Authorization": "Bearer " + api_key 
    }

response = requests.get(url, headers=headers)

print(response.text)