from flask import Flask, render_template, jsonify
from tmdb_client import fetch_movie_list

app = Flask(__name__)

# This is our queue of movies to display the users
MOVIE_QUEUE = []

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/get-next-movie')
def get_next_movie():
    global MOVIE_QUEUE
    
    # If the list is empty, refill it from the API
    if not MOVIE_QUEUE:
        print("Queue empty! Fetching new movies from TMDB...")
        MOVIE_QUEUE = fetch_movie_list()
    
    # If we have movies, "pop" the first one off the list
    if MOVIE_QUEUE:
        single_movie = MOVIE_QUEUE.pop(0) # Removes from list and stores in variable
        return jsonify(single_movie)
    
    return jsonify({"error": "No movies available"}), 404

if __name__ == '__main__':
    app.run(debug=True)