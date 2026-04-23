


#these are given their own file to stop dependency imports on the pypod submission side.


# WORKFLOW STEPS allows buttons that submit jobs to the POD code to be
# added or removed by editing this config file instead of modifying backend logic.
# However, actions that are not simple job submissions must still be handled
# manually in the /workflow route. Any workflow-state outputs that require
# special handling must also be implemented in the /workflow-state route.

# Updating this dict ensures the backend logic stays consistent, but the
# corresponding JavaScript and HTML for the buttons must still be updated manually. a JS funct is provided to help with this


WORKFLOW_STEPS = {
    "compute_A": { #name of the button 
        "label": "Compute A Matrix", #label used in flask backend
        "task": "calculate_A", #task applied to the backend POD program
        "required": ["last_floorplan", "last_fem"],#requirements for this button to appear
        "forbidden": [], #what other buttons will prevent this button from being on
        "resets": ["have_A_matrix", "have_eigenvalues", "looked_at_eigen",#DB values for user that get overwritten when button is used
                   "have_pod_modes", "have_C_matrix", "have_G_matrix",
                   "have_P_matrix", "have_ODE_sol",],
        "on_complete": "have_A_matrix",#DB value to update on completion
        "submits_job": True,#whether this submits a job or not
    },
    "get_eigenvalue": {
        "label": "Get Eigenvalues",
        "task": "get_eigenvalue",
        "required": ["have_A_matrix"],
        "forbidden": ["have_eigenvalues", "have_pod_modes", "have_C_matrix", "have_G_matrix"],
        "resets": ["have_eigenvalues", "looked_at_eigen", "have_pod_modes",
                   "have_C_matrix", "have_G_matrix", "have_P_matrix", "have_ODE_sol"],
        "on_complete": "have_eigenvalues",
        "submits_job": True,
    },
    "view_eigen": {
        "label": "View Eigenvalues",
        "task": None,
        "required": ["have_eigenvalues"],
        "forbidden": [],
        "resets": [],
        "on_complete": "looked_at_eigen",
        "submits_job": False,
    },
    "train_POD": {
        "label": "Train POD",
        "task": "train_POD",
        "required": ["have_A_matrix", "have_eigenvalues", "looked_at_eigen"],
        "forbidden": ["have_pod_modes", "have_C_matrix", "have_G_matrix"],
        "resets": ["have_pod_modes", "have_C_matrix", "have_G_matrix",
                   "have_P_matrix", "have_ODE_sol"],
        "on_complete": "have_pod_modes",
        "submits_job": True,
    },
    "calculate_C": {
        "label": "Calculate C Matrix",
        "task": "calculate_C",
        "required": ["have_A_matrix", "have_eigenvalues", "looked_at_eigen", "have_pod_modes"],
        "forbidden": ["have_C_matrix"],
        "resets": ["have_C_matrix", "have_P_matrix", "have_ODE_sol"],
        "on_complete": "have_C_matrix",
        "submits_job": True,
    },
    "calculate_G": {
        "label": "Calculate G Matrix",
        "task": "calculate_G",
        "required": ["have_A_matrix", "have_eigenvalues", "looked_at_eigen", "have_pod_modes"],
        "forbidden": ["have_G_matrix"],
        "resets": ["have_G_matrix", "have_P_matrix", "have_ODE_sol"],
        "on_complete": "have_G_matrix",
        "submits_job": True,
    },
    "calculate_P": {
        "label": "Calculate P Matrix",
        "task": "calculate_P",
        "required": ["have_A_matrix", "have_eigenvalues", "looked_at_eigen", "have_pod_modes",
                     "last_power_trace", "have_G_matrix", "have_C_matrix"],
        "forbidden": [],
        "resets": ["have_P_matrix", "have_ODE_sol"],
        "on_complete": "have_P_matrix",
        "submits_job": True,
    },
    "solve_ODE": {
        "label": "Solve ODE",
        "task": "solve_ODE",
        "required": ["have_A_matrix", "have_eigenvalues", "looked_at_eigen", "have_pod_modes",
                     "last_power_trace", "have_G_matrix", "have_C_matrix", "have_P_matrix",],
        "forbidden": ["have_ODE_sol"],
        "resets": ["have_ODE_sol"],
        "on_complete": "have_ODE_sol",
        "submits_job": True,
    },
    "post_process": { #just updates the post process button for clicking
        "label": "Post Processing",
        "task": None,
        "required": ["have_A_matrix", "have_eigenvalues", "looked_at_eigen", "have_pod_modes",
                     "last_power_trace", "have_G_matrix", "have_C_matrix",
                     "have_P_matrix", "have_ODE_sol"],
        "forbidden": [],
        "resets": None,
        "on_complete": None,
        "submits_job": True,
    },
}


POST_STEPS = {
    "post_process_all": {
        "label": "Post Processing",
        "task": "post_process_all",
        "required": ["have_A_matrix", "have_eigenvalues", "looked_at_eigen", "have_pod_modes",
                     "last_power_trace", "have_G_matrix", "have_C_matrix",
                     "have_P_matrix", "have_ODE_sol"],
        "forbidden": [],
        "resets": ["whole_mesh_processed"],
        "on_complete": "whole_mesh_processed",
        "submits_job": True,
    },
    "download_whole_mesh": {
        "label": "download whole mesh",
        "task": None,
        "required": ["whole_mesh_processed"],
        "forbidden": [],
        "resets": [],
        "on_complete": None,
        "submits_job": False,
    }
}
