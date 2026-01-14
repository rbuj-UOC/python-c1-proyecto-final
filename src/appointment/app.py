import os
from flask import Flask
from flask_cors import CORS
from cites_bp import cites_bp
from database import init_db

app = Flask(__name__)
CORS(app)

# Inicialitzar BD
with app.app_context():
    init_db()

# Registrar blueprint
app.register_blueprint(cites_bp, url_prefix="/cites")


@app.route("/")
def hello():
    return {"message": "Appointment Service API", "status": "running"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
