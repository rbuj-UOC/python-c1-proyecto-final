import os
from flask import Flask
from flask_cors import CORS
from login import login_bp
from verify import verify_bp

app = Flask(__name__)
CORS(app)

# Registrar blueprints amb prefix /auth
app.register_blueprint(login_bp, url_prefix="/auth")
app.register_blueprint(verify_bp, url_prefix="/auth")


@app.route("/")
def hello():
    return {"message": "Auth Service API", "status": "running"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)
