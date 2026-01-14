import os
from flask import Flask
from flask_cors import CORS
from auth_bp import auth_bp
from users_bp import users_bp
from database import init_db, create_default_admin

app = Flask(__name__)
CORS(app)

# Inicialitzar la base de dades i crear usuari per defecte
with app.app_context():
    init_db()
    create_default_admin()

# Registrar blueprints amb prefix /auth i /admin
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(users_bp, url_prefix="/admin")


@app.route("/")
def hello():
    return {"message": "Auth Service API", "status": "running"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)
