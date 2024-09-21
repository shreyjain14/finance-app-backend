from flask import Flask, jsonify
from os import path, getenv
from dotenv import load_dotenv
from .extentions import db, cors, jwt
from .models import User, TokenBlocklist
from datetime import timedelta

load_dotenv()


def create_app():
    app = Flask(__name__)

    # app configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URI')
    app.config['SECRET_KEY'] = getenv('SECRET_KEY')
    app.config["JWT_SECRET_KEY"] = getenv('JWT_SECRET')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=365)

    # extensions initialization
    db.init_app(app)
    jwt.init_app(app)

    cors.init_app(app, resources={r"/*": {
        "origins": [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://shrey-finance.toystackapp.net"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True  # If you're using cookies or authentication
    }})

    # creating db if not exists
    from . import models

    if not path.exists('instance/db.sqlite3'):
        with app.app_context():
            db.create_all()

    # registering blueprints
    from .api_auth import api_auth
    from .api_payment import api_payment

    app.register_blueprint(api_auth, url_prefix='/auth/')
    app.register_blueprint(api_payment, url_prefix='/payment/')

    # load user
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_headers, jwt_data):
        identity = jwt_data["sub"]

        return User.query.filter_by(username=identity).one_or_none()

    # additional claims

    @jwt.additional_claims_loader
    def make_additional_claims(identity):
        if identity == "janedoe123":
            return {"is_staff": True}
        return {"is_staff": False}

    # jwt error handlers

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return jsonify({"message": "Token has expired", "error": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed", "error": "invalid_token"}
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "message": "Request doesnt contain valid token",
                    "error": "authorization_header",
                }
            ),
            401,
        )

    @jwt.token_in_blocklist_loader
    def token_in_blocklist_callback(jwt_header, jwt_data):
        jti = jwt_data['jti']

        token = db.session.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).scalar()

        return token is not None

    return app
