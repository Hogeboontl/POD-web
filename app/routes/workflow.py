from flask import request, jsonify, redirect, url_for, session, Response, stream_with_context, Blueprint, render_template
from sqlalchemy.orm.attributes import flag_modified
import redis
import json
import torch
import plotly.graph_objects as go
from app.models.models import Training_Data, Code_Configs, User
from app.services.file_service import get_user_dir
from app.extensions import db
from config import config_args
import math
from app.settings.settings import CORE_MAX, RAM_MAX, CELERY_LOCATION

import sys
sys.path.append(CELERY_LOCATION)

from tasks import submit_and_monitor_job, WORKFLOW_GROUPS
from celery import chain

import uuid

def get_step(action):
    for group,_ in WORKFLOW_GROUPS:
        if action in group:
            return group[action]
    return None

workflow_bp = Blueprint("workflow", __name__)


#handles all workflow submissions (aka sends out jobs and displays values for special cases)
@workflow_bp.route('/workflow', methods=['POST'])
def work_flow():
    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))
    action = request.get_json()
    step = get_step(action)
    if not step:
        return jsonify({"error": "unknown action"}), 400

    email = session["email"]
    training_row = db.session.query(Training_Data).filter_by(email=email).first()
    config_row   = db.session.query(Code_Configs).filter_by(email=email, is_active=True).first()
    config = config_row.config

    # Apply resets
    for field in (step["resets"] or []):
        setattr(training_row, field, False)

    # Special non-job actions (e.g. view_eigen)
    if action == "view_eigen":
        db.session.commit()
        temp = config["save-dir"] + "eigenstuff.pt"
        eigenstuff = torch.load(temp)
        eigenvalues = eigenstuff["L"].numpy()
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=eigenvalues, mode='lines+markers'))
        fig.update_layout(title="Eigenvalues vs Mode Number", yaxis_type="log",
                          xaxis_title="Mode Number", yaxis_title="Eigenvalue")
        return jsonify({"plot": json.loads(fig.to_json())})

    #create request_ID for user job
    request_id = str(uuid.uuid4())
    # Submit slurm job
    if step["submits_job"]:
        r = redis.Redis()
        config["task"] = step["task"]

        submit_and_monitor_job.delay(
            email=email,
            upload_dir=config_row.upload_dir,
            config=config,
            request_id = request_id
        ) 


    db.session.commit()
    return jsonify({"status": "submitted"})

# updates workflow state for special cases that dont involve submitting jobs.
@workflow_bp.route('/workflow-state', methods=['POST'])
def workflow_state():
    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))

    email = session["email"]
    action = request.get_json()  # e.g. "a_mat_complete"
    training_row = db.session.query(Training_Data).filter_by(email=email).first()     

    if action == "looked_at_eigen_complete":
        already_trained = any((training_row.have_G_matrix, training_row.have_C_matrix,
                                training_row.have_pod_modes, training_row.have_P_matrix))

        training_row.looked_at_eigen = True  
        db.session.commit()
        return jsonify({"training_needed": already_trained})

    if action in ("check_p_matrix_ready"):
        row = db.session.query(Code_Configs).filter_by(email=email, is_active=True).first()

        return jsonify({
            "have_G_matrix": training_row.have_G_matrix,
            "have_C_matrix": training_row.have_C_matrix,
            "have_power_trace": row.last_power_trace is not None
        })

    return jsonify({"status": "ok"})



@workflow_bp.route('/job-status-stream')
def job_status_stream():
    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))

    email = session["email"]

    def event_stream():
        r = redis.Redis()
        pubsub = r.pubsub()
        terminal = {"COMPLETED", "FAILED", "CANCELLED", "SUBMIT_FAILED", "ERROR"}

        try:
            request_id_bytes = r.get(f"current_request:{email}")
            if not request_id_bytes:
                yield f"data: NO_JOB\n\n"
                return

            request_id = request_id_bytes.decode()


            seen = set()

            # Replay Celery cache first (SUBMITTED/CANCELLED/SUBMIT_FAILED)
            for item in r.lrange(f"job_status_cache:{request_id}", 0, -1):
                parts = item.decode().split(":")
                if len(parts) < 3:
                    continue
                status, _, msg_request_id = parts
                if msg_request_id != request_id:
                    continue
                if status not in seen:
                    seen.add(status)
                    yield f"data: {status}\n\n"
                if status in terminal:
                    return

            # Replay script cache second (RUNNING/COMPLETED/FAILED)
            # This handles reconnects after job already finished
            for item in r.lrange(f"job_script_cache:{request_id}", 0, -1):
                parts = item.decode().split(":")
                if len(parts) < 3:
                    continue
                status, _, msg_request_id = parts
                if msg_request_id != request_id:
                    continue
                if status not in seen:
                    seen.add(status)
                    yield f"data: {status}\n\n"
                if status in terminal:
                    return  # job already done, no need to subscribe

            # Only subscribe if no terminal state found in either cache
            pubsub.subscribe(f"job_status:{email}")
            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=45)
                if message is None:
                    yield ": keepalive\n\n"
                    continue
                if message["type"] != "message":
                    continue
                parts = message["data"].decode().split(":")
                if len(parts) < 3:
                    continue
                status, _, msg_request_id = parts
                if msg_request_id != request_id:
                    continue
                if status not in seen:
                    seen.add(status)
                    yield f"data: {status}\n\n"
                if status in terminal:
                    break

        finally:
            pubsub.unsubscribe()
            pubsub.close()

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )


#this ensures the config is updated
#assumes that all options for one config option will produce the same type (i.e a config option cannot accept both an int and string value)
@workflow_bp.route('/update_config', methods=['POST'])
def update_config():

    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))

    email = session["email"] 

    data = request.get_json()

    # Fetch last config from DB
    row = db.session.query(Code_Configs).filter_by(email=email, is_active=True).first()

    # Update temp config
    for k, v in data.items():
        try:
            row.config[k] = type(config_args['training_config'][k][0])(v)
        except ValueError:
            return jsonify(row.config)


    # Save to MySQL 
    db.session.commit()

    return jsonify(row.config)

#adjust the server settings for cores and ram.
@workflow_bp.route("/adjust_server_settings",methods=['GET', 'POST'])
def adjust_server_settings():
    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))

    email = session["email"] 
    row = db.session.query(User).filter_by(email=email).first()


    if request.method == "POST":
        data = request.get_json()
        row.cores = data["cores"]
        row.memory_gb = data["mem"]
        db.session.commit()
        return jsonify({"Status": "ok"})


    # number of cores double for each option
    core_values = [1 * 2**val for val in range(math.floor(math.log(CORE_MAX, 2))+1)]
    
    return render_template("adjust_server_settings.html",  core_values = core_values, RAM_MAX = RAM_MAX, curr_core = row.cores, curr_mem = row.memory_gb)








