from flask import Flask
from routes import bp as routes_bp
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Update for production
CORS(app)  # Allows frontend to access backend resources

# Register the blueprint for routes
app.register_blueprint(routes_bp)

if __name__ == '__main__':
    app.run(debug=True)
