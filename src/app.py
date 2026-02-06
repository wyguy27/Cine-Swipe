from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    # This just checks if the 'templates' folder is working
    return "Welcome to Cine-Swipe" 

if __name__ == "__main__":
    app.run(debug=True)