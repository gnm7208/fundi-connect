"""Extensions initialization for Fundi Connect."""

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()
