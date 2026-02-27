from flask import Flask, render_template, jsonify, request
from tmdb_client import fetch_movie_list

app = Flask(__name__)

# This is our queue of movies to display the users
MOVIE_QUEUE = []
LIKED_MOVIE = []

# Home route that renders the main page of the app
@app.route('/')
def home():
    return render_template('index.html') # CHANGE TO HOME PAGE ONCE SET UP

# Sends the next movie in the queue to the frontend in JSON format
@app.route('/api/get-next-movie')
def get_next_movie():

    # queue of next movies to show
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

# Receive the user's input on whether they like or dislike the movie
@app.route('/api/vote', methods=['POST'])
def handle_vote():
    data = request.json 
    movie_id = data.get('id')
    vote_type = data.get('vote')  # 'like' or 'dislike'

    if vote_type == 'like':
        # Add to liked movies list
        LIKED_MOVIE.append(movie_id)

    return jsonify({"message": "Vote received", "liked_movies": LIKED_MOVIE})


    

if __name__ == '__main__':
    app.run(debug=True)