from flask import Flask, render_template, jsonify
from tmdb_client import get_movies # Import your cleaned-up function

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

# first function getting list of random movies and
@app.route('/api/movies')
def api_movies():
    movie_list = get_movies()
    return jsonify(movie_list)


if __name__ == '__main__':
    app.run(debug=True)