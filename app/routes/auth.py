from flask import Blueprint, redirect, url_for, session
from app.extensions import db, oauth
from app.models.models import User, Training_Data, Code_Configs
from app.settings.settings import save_dir,DISABLE_OAUTH_HTTPS
from app.services.file_service import get_user_dir
from config import config_args
import os



auth_bp = Blueprint("auth", __name__)




#disable https for development
if DISABLE_OAUTH_HTTPS:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"



@auth_bp.route("/login_with_github")
def login_with_github():
    return oauth.github.authorize_redirect(url_for('auth.after_login',_external=True))

#after login route, token is discarded, we just use OAuth to get a valid email
@auth_bp.route("/after_login")
def after_login():

    #grab the token
    token = oauth.github.authorize_access_token()

    #get user email
    resp = oauth.github.get('/user/emails', token = token)
    user_email = resp.json()

    #make sure there is no API error
    if "status" in user_email:
        if user_email["status"] != '200':
            flash("API request error")


    user_email = user_email[0]
    email = user_email["email"]
            
    # now safely store the email
    user = db.session.query(User).filter_by(email=email).first()
    if not user:
        user = User(email=email)
        db.session.add(user)
        db.session.commit()

    session["email"] = email

    #initialize important user tables
    training_row = db.session.query(Training_Data).filter_by(email=email).first()
    if not training_row:
        training_row = Training_Data(email=email)
        db.session.add(training_row)

    row = db.session.query(Code_Configs).filter_by(email=email).first()
    if not row:
        default_config = {param: value[0] for param, value in config_args['training_config'].items()}
        default_config["save-dir"] = get_user_dir(email,save_dir) + "/"
        row = Code_Configs(email=email, config=default_config, upload_dir=get_user_dir(email), is_active = True)
        db.session.add(row)
    db.session.commit()

    return redirect(url_for("upload.upload_file"))