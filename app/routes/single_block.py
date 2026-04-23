from flask import Blueprint, render_template, redirect, url_for, session

from app.extensions import db
from app.models.models import Training_Data, Code_Configs
from app.settings.settings import expected_files, excluded_configs
from config import config_args
from app.settings.workflow_settings import WORKFLOW_STEPS
from app.utils.has_flags import has_flag

single_block_bp = Blueprint("single_block", __name__)



#renders the single block page
@single_block_bp.route('/', methods=['GET'])
def render_single_block_page():
    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))

    email = session["email"]

    training_row = db.session.query(Training_Data).filter_by(email=email).first()

    row = db.session.query(Code_Configs).filter_by(email=email, is_active=True).first()

    buttons = {
        name: (
            all(has_flag(training_row, row, attr=f) for f in step["required"]) and
            not any(has_flag(training_row, row, attr=f) for f in step["forbidden"])
        )
        for name, step in WORKFLOW_STEPS.items()
    }
    #get file states from database
    file_states = {
        spec["training_flag"]: getattr(row, spec["training_flag"], None)
        for spec in expected_files.values()
    }

    return render_template( 'single_block.html', expected_files=expected_files, 
        config_args=config_args, 
        submitted_config=row.config,
        exclude = excluded_configs, 
        buttons=buttons,
        file_states = file_states)