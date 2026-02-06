import requests
import os 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()  # By default, looks for .env in the current directory

# Get the API key
api_key = os.getenv("TMDB_API_KEY")



url = "https://api.themoviedb.org/3/authentication"

headers = {
    "accept": "application/json",
    "Authorization": "Bearer " + api_key
}

response = requests.get(url, headers=headers)

print(response.text)