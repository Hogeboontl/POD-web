from flask_sqlalchemy import SQLAlchemy
from app.models.models import *
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy(model_class=Base)

#create OAuth
oauth = OAuth()