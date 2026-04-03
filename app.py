from flask import Flask, render_template, jsonify, request
import tmdb_client as tmdb

app = Flask(__name__)

# queue of movies to display the users
MOVIE_QUEUE = []

# lists to store the user's liked and disliked movies
LIKED_MOVIE = []
DISLIKED_MOVIE = []

# Home route that renders the main page of the app
@app.route('/')
def home():
    return render_template('homepage.html') # CHANGE TO HOME PAGE ONCE SET UP

@app.route('/start')
def start():
    return render_template('index.html')

# Gets the list of movie genres from API and sends it to the frontend in JSON format
@app.route('/api/genres')
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

    # queue of next movies to show
    global MOVIE_QUEUE, CURRENT_PAGE

    CURRENT_PAGE = 1
    
    filters = {
                    "include_adult": request.args.get('isAdult'),
                    "with_genres": request.args.get('genre'),
                    "with_language": request.args.get('lang'),
                    "page": CURRENT_PAGE
                }

    # If the list is empty, refill it from the API
    if not MOVIE_QUEUE:
        print("Queue empty! Fetching new movies from TMDB...")
        CURRENT_PAGE += 1
        MOVIE_QUEUE = tmdb.fetch_movie_list(filters)
    
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
    elif vote_type == 'dislike':
        # Add to disliked movies list
        DISLIKED_MOVIE.append(movie_id)

    return jsonify({"message": "Vote received", "liked_movies": LIKED_MOVIE, "disliked_movies": DISLIKED_MOVIE})




if __name__ == '__main__':
    app.run(debug=True)