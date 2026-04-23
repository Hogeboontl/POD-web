{

    // unique positions available on the mesh
    var ux;
    var uy;
    var uz;
    

    // polling display, provided per page
    const job_status = document.getElementById("status");

    const layout = {
        autosize: true,
        margin: { l: 40, r: 20, t: 20, b: 40 }
      };

    //initialize an empty plotly plot on the div so its not empty
    Plotly.newPlot('external', [], layout, {
        responsive: true
    }); 

    // will snap the user input position to the nearest available plane, assumes a structured box mesh.
    function snapToNearest(uniquePositions, value) {
    return uniquePositions.reduce((prev, curr) =>
        Math.abs(curr - value) < Math.abs(prev - value) ? curr : prev
    );
    }

    const BUTTONS = {
        post_process_all: document.getElementById("post_process_all"),
        download_mesh: document.getElementById("download_whole_mesh"),
        post_process_slice: document.getElementById("post_process_slice"),
        download_heatmap: document.getElementById("download_heatmap"),
        download_slice_temps: document.getElementById("download_slice_temps")
    };

    // MIMETYPE to actual extension name so users can see it when it downloads
    const extensionMap = {
        "application/zip": "zip",
        "text/csv": "csv",
        "application/json": "json",
        "image/png": "png"
      };



    // on loading this file, get all the unique coordinates 
    // the current post processing depends on a structured mesh so that user position inputs "snap" to planes, meaning no interpolation is done to keep this lightweight.
    // also resets all buttons not workflow related (since firefox doesnt do this automatically.)
    document.addEventListener("DOMContentLoaded", () => {
        fetch("/post_processing/get_snap_values")
        .then(resp => resp.ok && resp.json())
        .then( (data) => {
            ux = data.x;
            uy = data.y;
            uz = data.z;
        });
        BUTTONS.download_heatmap.disabled = true;
        BUTTONS.download_slice_temps.disabled = true;
        
    })





    BUTTONS.post_process_all.addEventListener("click", () => {
        submitWorkflowJob(BUTTONS.post_process_all, job_status,"post_process_all", () => {
            BUTTONS.download_mesh.disabled = false;
        });
    });

    BUTTONS.post_process_slice.addEventListener("click", () => {
        BUTTONS.post_process_slice.disabled = true;
        // post processing slice values 
        var post_time_step = document.getElementById("timestep-input").value;
        var axis = document.getElementById("axis-select").value;
        var position = document.getElementById("position-input").value;
        if (axis == 0) {
            position = snapToNearest(ux, position);
        }
        else if (axis == 1) {
            position = snapToNearest(uy, position); 
        }
        else {
            position = snapToNearest(uz, position); 
        }
        fetch("/post_processing/process_slice", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"post_time_step" : parseInt(post_time_step),
                                  "axis" : parseInt(axis),
                                  "position" : parseFloat(position)
            })
        })
        .then(resp => resp.ok && resp.json())
        .then( (data) => {
        Plotly.react('external', data, {}); 
        BUTTONS.post_process_slice.disabled = false;
        BUTTONS.download_heatmap.disabled = false;
        BUTTONS.download_slice_temps.disabled = false;
        });
    });
    
    BUTTONS.download_mesh.addEventListener("click", () => {
        BUTTONS.download_mesh.disabled = true;
        fetch('/process_download_items', {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"type": "zip"})
        })
       .then(resp => resp.status === 200 ? resp.blob() : Promise.reject('something went wrong'))
       .then(blob => {
         const url = window.URL.createObjectURL(blob);
         const a = document.createElement('a');
         a.style.display = 'none';
         a.href = url;
         // the filename you want
         a.download = 'full_mesh_temp_data';
         document.body.appendChild(a);
         a.click();
         window.URL.revokeObjectURL(url);
         alert('your file has downloaded!'); 
         BUTTONS.download_mesh.disabled = false;
       })
       .catch(() => {
        alert('oh no!');
       BUTTONS.download_mesh.disabled = false;
        });
    });

    BUTTONS.download_heatmap.addEventListener("click", () => {
        BUTTONS.download_heatmap.disabled = true;
        const gd = document.getElementById("external");
        Plotly.toImage(gd, {
            format: "png",
            width: 1200,
            height: 800
        })
        .then((dataUrl) => {
            var post_time_step = document.getElementById("timestep-input").value;
            var axis = document.getElementById("axis-select").value;
            var position = document.getElementById("position-input").value;
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = dataUrl;
            a.download = `${post_time_step}-${axis}-${position}_heatmap.png`;;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(dataUrl);
            alert('your file has downloaded!'); 
            BUTTONS.download_heatmap.disabled = false;

        })
        .catch(() => {
            alert('oh no!');
            BUTTONS.download_heatmap.disabled = false;

        })
    })

    BUTTONS.download_slice_temps.addEventListener("click", () => {
        BUTTONS.download_slice_temps.disabled = true;
        var post_time_step = document.getElementById("timestep-input").value;
        var axis = document.getElementById("axis-select").value;
        var position = document.getElementById("position-input").value;
        fetch('/process_download_items', {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"type": "heatmap",
                                "post_time_step" : parseInt(post_time_step),
                                  "axis" : parseInt(axis),
                                  "position" : parseFloat(position)})
        })
       .then(resp => resp.status === 200 ? resp.blob() : Promise.reject('something went wrong'))
       .then(blob => {
         const url = window.URL.createObjectURL(blob);
         const a = document.createElement('a');
         const mime = blob.type.split(";")[0];
         a.download = `heat_map_slice.${extensionMap[mime]}`;
         console.log(a.download)
         a.style.display = 'none';
         a.href = url;
         document.body.appendChild(a);
         a.click();
         window.URL.revokeObjectURL(url);
         alert('your file has downloaded!'); 
         BUTTONS.download_mesh.disabled = false;
       })
       .catch(() => {
        alert('oh no!');
        BUTTONS.download_heatmap.disabled = false;

        })
    });
    
}
