from sqlalchemy import URL
import sys
import os
from dotenv import load_dotenv

#loads .env file variables 
load_dotenv()


# --- machine settings ---

CORE_MAX = 32  #sets max number of cores the user is allowed to request, options will be lg(n). i.e 32,16,8,4,2,1
RAM_MAX =  45    #sets max amount of RAM the user is allowed to request, in GB.


DISABLE_OAUTH_HTTPS = (os.getenv('DISABLE_OAUTH_HTTPS', 'false').lower() == 'true')

# --- Deployment paths --
SLURM_RUNNER_DIR = os.getenv("SLURM_RUNNER_DIR")      #user directory for the user that will submit the slurm jobs, should be seperate from the web server user
CONFIG_DIR = os.getenv("CONFIG_DIR")                   #config directory of the POD code being ran
upload_dir = os.getenv("UPLOAD_DIR")                   #where user uploads should go
save_dir = os.getenv("SAVE_DIR")                       #where user saved data should go
CELERY_LOCATION = os.getenv("CELERY_LOCATION")         #location of the celery tasks

#create URL object for sqlalchemy to write to database
url_object = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PSSWD"),  
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB"),
)


#add or remove expected files that the user will need to upload
# it will automatically update the upload form from the partials
expected_files = {
    "filename": {
        "label": "FEM heat data",
        "ext": {".zip"},                         #allowed extensions
        "is_zip": True,                          # triggers zip extraction logic
        "config_key": "fem_file",                # key in row.config to update
        "training_flag": "last_fem",             # training_row field to update
        "resets": ["have_pod_modes"],            # training_row flags to set False
        "extraction_subdir": "extracted_FEM",   # only needed for zips
    },
    "filename2": {
        "label": "power trace",
        "ext": {".txt"},
        "is_zip": False,
        "config_key": "power_trace_file",
        "training_flag": "last_power_trace",
        "resets": ["have_P_matrix"],
    },
    "filename3": {
        "label": "floorplan",
        "ext": {".txt"},
        "is_zip": False,
        "config_key": "floorplan_file",
        "training_flag": "last_floorplan",
        "resets": ["have_pod_modes"],
    },
} 

#this code expects a config file similar in style to the one present in PyPOD
#config items to not display on the website for easier control, this used in the config box partial
excluded_configs = ['task','save-dir', 'fem_file','power_trace_file','floorplan_file','cuda','save']