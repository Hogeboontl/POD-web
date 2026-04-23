from flask import Flask, Blueprint, render_template, session, jsonify,send_file, request
from flask_sqlalchemy import SQLAlchemy
from app.models.models import *
from app.extensions import db, oauth
import os
import zipfile
import io
import torch
import numpy as np
import plotly.express as px
from scipy.interpolate import griddata
import redis
import json
from app.settings.workflow_settings import POST_STEPS
from app.utils.has_flags import has_flag

post_processing_bp = Blueprint('post_processing', __name__)

@post_processing_bp.route("/render_page")
def render_page():
    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))

    email = session["email"]
    training_row = db.session.query(Training_Data).filter_by(email=email).first()
    post_row = db.session.query(Post_Processing_Data).filter_by(email=email).first()
    config_row = db.session.query(Code_Configs).filter_by(email=email, is_active=True).first()

    buttons = {
        name: (
            all(has_flag(training_row, post_row, config_row, attr=f)
                for f in step["required"]) and

            not any(has_flag(training_row, post_row, config_row, attr=f)
                    for f in step["forbidden"])
        )
        for name, step in POST_STEPS.items()
    }

    return render_template('post_processing.html', buttons=buttons, config_args=config_row.config)

@post_processing_bp.route("/get_snap_values")
def get_snap_values():
    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))

    email = session["email"]
    row = db.session.query(Code_Configs).filter_by(email=email, is_active=True).first()
    save_dir = row.config["save-dir"]
    #load dof to coordinate mapping
    dof_coords = np.load(f'{save_dir}dof_coords.npy', allow_pickle=True)
    #get unique values on each axis
    ux = np.unique(dof_coords[:, 0])
    uy = np.unique(dof_coords[:, 1])
    uz = np.unique(dof_coords[:, 2])
    return jsonify({"x" : ux.tolist(),
                    "y": uy.tolist(),
                    "z": uz.tolist()})


#post_processing just a slice on one time step should be fast enough for the backend to do it.
#otherwise the latency of submitting a job will be terrible for each time step.
#also this snaps to the nearest plane, so without interpolation the calculations are relatively cheap.
@post_processing_bp.route("/process_slice",  methods=["POST"])
def process_slice():

    if "email" not in session:
        return redirect(url_for("auth.login_with_github"))
    email = session["email"]



    #open redis cache
    r = redis.Redis()

    #parse the data
    data = request.get_json()

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

    #if cache has it, return it 
    if cached_value:
        temp = json.loads(cached_value)
        fig = temp["fig"]
        return fig
    
    #otherwise, load and do the math
    dof_coords = np.load(f'{save_dir}dof_coords.npy', allow_pickle=True)

    # set nu to 1 since we are getting modes over the whole chip
    Nu = 1

    # number of modes and total time steps from config
    num_modes = config["num-modes"]
    time_steps = config["time-steps"]


    #load data from user directory
    CU = torch.load(f'{save_dir}CU.pt')

    mode_stuff = torch.load(f'{save_dir}POD_modes.pt')
    modes_data = mode_stuff['modes_data']

    #reshape as detailed from original code
    CU = CU.reshape(Nu, time_steps, num_modes)
    #take only our time step
    CU = CU[:,post_time_step,:]


    # use exact equality on the snapped value
    mask = dof_coords[:, axis] == position
    indices = np.where(mask)[0]

    if len(indices) == 0:
        return jsonify({"error": "No DOFs found"}), 400

    modes_data = modes_data[:,indices]

    #predict thermal
    x = CU[0].reshape(-1, 1)                          # (num_modes, 1)
    temps = (modes_data * x).sum(dim=0).detach().numpy()

    #make heatmap of temps for the slice

    plot_axes = [ax for ax in [0, 1, 2] if ax != axis]
    plot_coords = dof_coords[indices][:, plot_axes]


    grid_x, grid_y = np.mgrid[
        plot_coords[:, 0].min():plot_coords[:, 0].max():300j,
        plot_coords[:, 1].min():plot_coords[:, 1].max():300j
    ]

    grid_temps = griddata(
        points=plot_coords,
        values=temps,
        xi=(grid_x,grid_y),
        method='linear',    # 'nearest' if you get too many NaNs at edges
        fill_value=np.nan
    )

    fig = px.imshow(
        grid_temps.T,
        origin='lower',
        color_continuous_scale='Thermal',
        labels={'color': 'Temperature'},
        aspect='auto',
        x=np.linspace(plot_coords[:, 0].min(), plot_coords[:, 0].max(), 300),
        y=np.linspace(plot_coords[:, 1].min(), plot_coords[:, 1].max(), 300),
    )

    #serialize python dict
    value = json.dumps({
    "fig": fig.to_json(),
    "temps": temps.tolist(),
    "dof" : dof_coords[mask].tolist(),
    })

    r.set(key,value, ex = 600) #key is valid for 10 minutes, helps ensure that if a user recomputes, the previous cache should be wiped, but we make sure in the key anyways

    return fig.to_json()




