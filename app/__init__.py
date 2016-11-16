from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_bootstrap import Bootstrap
from flask_pagedown import PageDown
from flask_login import LoginManager

db = SQLAlchemy()
bootstrap = Bootstrap()
pagedown = PageDown()
Login_manager = LoginManager()
Login_manager.session_protection = "strong"
Login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    from .main import main as main_blueprint
    from .auth import auth as auth_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    db.init_app(app)
    bootstrap.init_app(app)
    pagedown.init_app(app)
    Login_manager.init_app(app)

    return app