{

    // Maps step name -> button element
    // insert new buttons here, one of these needs to be provided per page
    const BUTTONS = {
    compute_A:      document.getElementById("A-mat-btn"),
    get_eigenvalue: document.getElementById("eigenvalue"),
    view_eigen:     document.getElementById("view-eigen"),
    train_POD:      document.getElementById("train-btn"),
    calculate_C:    document.getElementById("C-mat-btn"),
    calculate_G:    document.getElementById("G-mat-btn"),
    calculate_P:    document.getElementById("P-mat-btn"),
    solve_ODE:      document.getElementById("simulate-btn"),
    post_process_all: document.getElementById("post-process-btn"),
    };
    
    window.BUTTONS = BUTTONS //defines buttons for the entire single block page

    // polling display, provided per page
    const job_status = document.getElementById("status");

    
    // button function use
    
    BUTTONS.compute_A.addEventListener("click", () => {
        submitWorkflowJob(BUTTONS.compute_A, job_status, "compute_A", () => {
            BUTTONS.get_eigenvalue.disabled = false;
        });
    });
    
    BUTTONS.get_eigenvalue.addEventListener("click", () => {
        submitWorkflowJob(BUTTONS.get_eigenvalue,job_status, "get_eigenvalue", () => {
            BUTTONS.view_eigen.disabled = false;
        });
    });
    
    // view_eigen is special - no job submission, opens popup
    BUTTONS.view_eigen.addEventListener("click", () => {
        fetch("/workflow", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify("view_eigen")
        })
        .then(res => res.json())
        .then(data => {
            const popup = window.open('', '_blank', 'width=800,height=500');
            popup.document.write(`
                <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
                <div id="plot" style="width:100%;height:100%"></div>
                <script>
                    Plotly.newPlot('plot', ${JSON.stringify(data.plot.data)}, ${JSON.stringify(data.plot.layout)});
                </script>
            `);
        })
        .then(() => fetch("/workflow-state", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify("looked_at_eigen_complete")
        }))
        .then(res => res.json())
        .then(data => {
            if (!data.training_needed) BUTTONS.train_POD.disabled = false;
        });
    });
    
    BUTTONS.train_POD.addEventListener("click", () => {
        submitWorkflowJob(BUTTONS.train_POD,job_status, "train_POD", () => {
            BUTTONS.calculate_C.disabled = false;
            BUTTONS.calculate_G.disabled = false;
        });
    });
    
    // C and G share the same completion check
    function checkPMatrixReady() {
        setTimeout(() => {
            fetch("/workflow-state", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify("check_p_matrix_ready")
            })
            .then(res => res.json())
            .then(data => {
                if (data.have_G_matrix && data.have_C_matrix && data.have_power_trace) {
                    BUTTONS.calculate_P.disabled = false;
                }
            });
        }, 2000) //prevents race condition on the db, needs to be improved to depend on stream.
        
    }
    
    
    
    
    BUTTONS.calculate_C.addEventListener("click", () => {
        submitWorkflowJob(BUTTONS.calculate_C,job_status, "calculate_C", checkPMatrixReady);
    });
    
    BUTTONS.calculate_G.addEventListener("click", () => {
        submitWorkflowJob(BUTTONS.calculate_G,job_status, "calculate_G", checkPMatrixReady);
    });
    
    BUTTONS.calculate_P.addEventListener("click", () => {
        submitWorkflowJob(BUTTONS.calculate_P,job_status, "calculate_P", () => {
            BUTTONS.solve_ODE.disabled = false;
        });
    });
    
    BUTTONS.solve_ODE.addEventListener("click", () => {
        submitWorkflowJob(BUTTONS.solve_ODE,job_status, "solve_ODE", () => {
            BUTTONS.post_process_all.disabled = false;
        });
    });



    //adjust server button, should probably be moved for clarity.
    document.getElementById("adjust-server-settings").addEventListener("click", () => {
        window.open('/adjust_server_settings',null,"height=500,width=500,status=yes,toolbar=no,menubar=no,location=no");
    })

}