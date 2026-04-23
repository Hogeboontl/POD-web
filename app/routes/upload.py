from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session,send_file
from werkzeug.utils import secure_filename
from sqlalchemy.orm.attributes import flag_modified
import os, zipfile, shutil, re
import io

from app.extensions import db
from app.models.models import Training_Data, Code_Configs
from app.settings.workflow_settings import WORKFLOW_STEPS
from app.settings.settings import expected_files, excluded_configs
from app.services.file_service import get_user_dir
from config import config_args  # external
import redis
import numpy as np
import json
from app.utils.has_flags import has_flag


upload_bp = Blueprint("upload", __name__)

#handles uploads and updates values in single block database accordingly
@upload_bp.route('/', methods=['POST'])
def upload_file():

    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))
    email = session["email"]

    training_row = db.session.query(Training_Data).filter_by(email=email).first()

    row = db.session.query(Code_Configs).filter_by(email=email, is_active=True).first()

    just_uploaded = []
    failed_files = []

    for file_number, spec in expected_files.items():
        f = request.files.get(file_number)
        if f is None or f.filename == "":
            continue

        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in spec["ext"]:
            failed_files.append(f"{spec['label']} (invalid extension: {ext})")
            continue

        safe_name = secure_filename(f.filename)
        if not safe_name:
            failed_files.append(f"{spec['label']} (invalid filename)")
            continue

        path = os.path.join(row.upload_dir, safe_name)

        if spec["is_zip"]:
            f.save(path)
            extraction_directory = os.path.join(row.upload_dir, spec["extraction_subdir"])
            if os.path.exists(extraction_directory):
                shutil.rmtree(extraction_directory)
            os.makedirs(extraction_directory, exist_ok=True)

            MAX_UNCOMPRESSED_SIZE = 1 * 1024 * 1024 * 1024 * 1024
            safe_dir = os.path.realpath(extraction_directory) + os.sep
            with zipfile.ZipFile(path, 'r') as zip_ref:
                members = zip_ref.infolist()
                if sum(m.file_size for m in members) > MAX_UNCOMPRESSED_SIZE:
                    raise ValueError(f"Zip too large when extracted")
                bytes_written = 0
                for member in members:
                    parts = member.filename.split('/', 1)
                    if len(parts) < 2 or not parts[1]:
                        continue
                    member.filename = parts[1]
                    member_path = os.path.realpath(os.path.join(extraction_directory, member.filename))
                    if not member_path.startswith(safe_dir):
                        raise ValueError(f"Zip slip detected: {member.filename}")
                    if bytes_written > MAX_UNCOMPRESSED_SIZE:
                        shutil.rmtree(extraction_directory)
                        raise ValueError("Zip extraction exceeded size limit")
                    zip_ref.extract(member, extraction_directory)
                    bytes_written += os.path.getsize(member_path)
            os.remove(path)

            with os.scandir(extraction_directory) as it:
                first_file_name = next((e.name for e in it if e.is_file()), None)
            if first_file_name:
                match = re.match(r"[^\d]+", first_file_name)
                if match:
                    row.config[spec["config_key"]] = extraction_directory + '/' + match.group()
                    flag_modified(row, "config")
            just_uploaded.append(safe_name)

        else:
            # remove old file safely before saving new one
            old_path = row.config.get(spec["config_key"])
            if old_path:
                old_path = os.path.realpath(old_path)
                if os.path.isfile(old_path) and old_path.startswith(os.path.realpath(row.upload_dir)):
                    os.remove(old_path)

            f.save(path)
            just_uploaded.append(safe_name)
            row.config[spec["config_key"]] = os.path.join(row.upload_dir, safe_name)
            flag_modified(row, "config")

        # filenames go on row (Code_Configs), booleans go on training_row (Training_Data)
        setattr(row, spec["training_flag"], safe_name if not spec["is_zip"] else f.filename)
        for flag in spec["resets"]:
            setattr(training_row, flag, False)

    db.session.commit()

    upload_flags = {spec["training_flag"] for spec in expected_files.values()}

    button_states = {
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

    messages = []
    if just_uploaded:
        messages.append("Uploaded: " + ", ".join(just_uploaded))
    if failed_files:
        messages.append("Failed: " + ", ".join(failed_files))

    msg_type = "success"
    if failed_files and just_uploaded:
        msg_type = "warning"
    elif failed_files:
        msg_type = "error"

    return jsonify({
        "message": "\n".join(messages),
        "status": msg_type,
        "file_states": file_states,
        "buttons": button_states
    })



#handles processing items to be downloaded by user
#could benefit from generalization
@upload_bp.route("/process_download_items", methods=['POST'])
def process_download_items():
    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))
    email = session["email"]

    data = request.get_json()

    method = data["type"]

    if method == "zip":
        row = db.session.query(Code_Configs).filter_by(email=email, is_active=True).first()
        save_dir = row.config["save-dir"]


        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w") as archive:
                archive.write(f'{save_dir}dof_coords.npy', arcname = "dof_coords.npy")
                if os.path.exists(f'{save_dir}temps.txt'):
                    archive.write(f'{save_dir}temps.txt', arcname = "temps.txt")
                else: 
                    archive.write(f'{save_dir}temps.csv', arcname = "temps.csv")

        buf.seek(0)
        return send_file(buf,download_name = "download.zip")

    #grabs precomputed heatmap values from cache
    if method == "heatmap":
        r = redis.Redis()

        #grab the config values
        row = db.session.query(Code_Configs).filter_by(email=email, is_active=True).first()
        config = row.config
        save_dir = row.config["save-dir"]
        fem = config["fem_file"]
        power_trace = config["power_trace_file"]
        floorplan = config["floorplan_file"]

        #time step we want 
        post_time_step = int(data["post_time_step"])

        #axis and position we want
        axis = int(data["axis"])
        position = float(data["position"])

        #generate the cache key
        key = f"user_post_slice:{email}:{post_time_step}:{axis}:{position}:{fem}:{power_trace}:{floorplan}"
        #check if key exists 
        cached_value = r.get(key)

        #if cache has it, zip it and rip it  
        if cached_value:
            buf = io.BytesIO()
            cached_value = json.loads(cached_value)
            temps = cached_value["temps"]
            dofs = cached_value["dof"]

            if config["save-format"] == "txt":
                with zipfile.ZipFile(buf, mode="w") as archive:
                    archive.writestr("temps.txt", "\n".join(str(v) for v in temps))
                    archive.writestr("dofs.txt",  "\n".join(str(v) for v in dofs))

                buf.seek(0)
                return send_file(buf, download_name="heatmap_slice.zip", mimetype = "application/zip")

            if config["save-format"] == "csv":
                    buf.write("\n".join(f"{t},{d}" for t, d in zip(temps, dofs)).encode())
                    buf.seek(0)
                    return send_file(buf, download_name="heatmap_slice.csv", mimetype = "text/csv")


    
                

            
            

