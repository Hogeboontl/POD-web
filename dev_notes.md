
## Architecture Decisions
This code currently uses server side rendering, as the complexity grows, switching to Hybrid rendering may be advisable, however this would be a heavy rewrite.



### Backend Language
Python was chosen for straightforward plotting via Plotly/PyTorch and 
familiarity with the scientific stack. The primary concurrency concern is SSE 
streams holding open connections during long Slurm jobs — this is mitigated with 
gevent rather than requiring a full rewrite in Go or Rust. If concurrent job 
volume grows significantly, a migration could be reconsidered.

---

### Adding Workflow Steps
New computational steps can be added by editing `backend_config.py` rather than modifying the routing logic directly. This covers standard job submission steps. Tasks requiring custom output handling, such as rendering plots or returning specialized data, will still need to be implemented manually in the `/workflow` route.

For example, adding a button that truncates the whole workflow into one or two buttons can easily be done via the config.

A javascript function is also available to shorten this process, so that all that needs to be done is to add the button and call the function with the correct
parameters.

### Adding Upload Files
The file upload form is driven by the `expected_files` dictionary in `backend_config.py`. Adding a new file type requires only adding an entry to that dictionary and adding the corresponding column to the database model. If multiple upload presets are needed, they can be wrapped in separate dictionaries and selected via a database flag.

### Supporting Multiple Configurations
The config system is designed to eventually support multiple presets per user via adding to the database.


### Known bugs
 * currently for linux and mac machines, the number forms allow for character inputs. This may be fixable by switching to WTF-forms.


### ideas for things to add
 * file chunking during downloading as well as making it timeout safe
 * optimizing the forms using WTF-forms 
 * A whitelist/ whole login page on top of the OAuth features
 * small 3d rendering plot to show which plane of the mesh they are viewing.









