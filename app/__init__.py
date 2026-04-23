def create_app():
    from flask import Flask
    from app.extensions import db, oauth
    from app.settings.settings import url_object, upload_dir, save_dir,CONFIG_DIR, SLURM_RUNNER_DIR
    import os
    import sys
    from werkzeug.middleware.proxy_fix import ProxyFix
    from dotenv import load_dotenv

    #loads .env file variables 
    load_dotenv()
    upload_dir = os.getenv('UPLOAD_DIR')
    save_dir = os.getenv('SAVE_DIR')


    
    app = Flask(__name__)

    app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_port=1
    )

    oauth.init_app(app)
    
    oauth.register(
        name = "github",
        client_id = os.getenv("CLIENT_ID"),  
        client_secret = os.getenv("CLIENT_SECRET"), 
        access_token_url = "https://github.com/login/oauth/access_token",
        access_token_params=None,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        client_kwargs={'scope': 'user'},
        api_base_url = "https://api.github.com"


    )

    # --- Add paths needed for imports ---
    if CONFIG_DIR not in sys.path:
        sys.path.append(CONFIG_DIR)
    from config import config_args

    if SLURM_RUNNER_DIR not in sys.path:
        sys.path.insert(0, SLURM_RUNNER_DIR)
    if CONFIG_DIR not in sys.path:
        sys.path.append(CONFIG_DIR)

    app.config["SQLALCHEMY_DATABASE_URI"] = url_object
    app.secret_key = os.getenv("SECRET_KEY")

    #ensure directories are made
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(save_dir, exist_ok=True)

    #initialize db
    db.init_app(app)

    #create dbs if needed
    with app.app_context():
        db.create_all()

    # register blueprints
    from app.routes.workflow import workflow_bp
    from app.routes.postprocessing import post_processing_bp
    from app.routes.upload import upload_bp
    from app.routes.auth import auth_bp
    from app.routes.single_block import single_block_bp

    app.register_blueprint(workflow_bp)
    app.register_blueprint(single_block_bp)
    app.register_blueprint(post_processing_bp, url_prefix="/post_processing")
    app.register_blueprint(upload_bp)
    app.register_blueprint(auth_bp)

    return app

app = create_app()