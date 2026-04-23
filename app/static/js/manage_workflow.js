
const TERMINAL_STATES = ["FAILED", "SUBMIT_FAILED", "ERROR"];

// Generic job submission + SSE listener
//btn - the button you want the workflow to include
//polling display, optionally display the status of the button to a text value
// completionkey, what each task should send to the back end, i.e what value to update in the database
//stepName, name of the workflow task
// oncomplete, function that details what to do after completion (i.e what buttons to enable.disable)
// onfail, function for what to do on fail
function submitWorkflowJob(btn, polling_display = null, stepName, onComplete, onFail) {
    btn.disabled = true;

    const statusQueue = [];
    let isDisplaying = false;

    function displayNext() {
        if (statusQueue.length === 0) {
            isDisplaying = false;
            return;
        }
        isDisplaying = true;
        const { status, action } = statusQueue.shift();
        
        if (polling_display != null) {
            polling_display.textContent = status;
        }
        
        setTimeout(() => {
            action();
            displayNext();
        }, 2000);
    }

    function enqueue(status, action) {
        statusQueue.push({ status, action });
        if (!isDisplaying) displayNext();
    }


    const submit = () => fetch("/workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(stepName)
    }).then(() => {
        if (window.activeJobStream) window.activeJobStream.close();

        const es = new EventSource("/job-status-stream");
        window.activeJobStream = es;

        es.onmessage = (e) => {
            const status = e.data;

            if (status.startsWith("CANCELLED_PREVIOUS")) {
                enqueue("Cancelled previous job, submitting new job...", () => {});

            } else if (status === "COMPLETED") {
                es.close();
                window.activeJobStream = null;
                enqueue("COMPLETED", () => {
                    onComplete();
                });
            
            } else if (TERMINAL_STATES.includes(status)) {
                es.close();
                window.activeJobStream = null;
                enqueue(status, () => {
                    btn.disabled = false;
                    if (onFail) onFail();
                });

            } else {
                enqueue(status, () => {});
            }
        };
    });

    submit();
}










  