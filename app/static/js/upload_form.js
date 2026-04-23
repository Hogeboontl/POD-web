{
    const uploadForm = document.getElementById("upload-form");
    const uploadMessage = document.getElementById("upload-message");

    uploadForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        uploadMessage.textContent = "uploading..."

        fetch("/", { method: "POST", body: formData })
            .then(r => r.json())
            .then(data => {
                uploadMessage.innerText = data.message;
                uploadMessage.className = data.status;

                // update all button states from dict
                for (const [name, enabled] of Object.entries(data.buttons)) {
                    const btn = BUTTONS[name];
                    if (btn) btn.disabled = !enabled;
                }

                // update file display from dict
                for (const [flag, filename] of Object.entries(data.file_states)) {
                    console.log(flag, filename, document.getElementById(flag));
                    const el = document.getElementById(flag);
                    if (el) el.textContent = filename || '';
                }

                uploadForm.reset();
            })
            .catch(err => {
                uploadMessage.innerText = "Upload failed: " + err;
                uploadMessage.className = "error";
            });
    });

    document.getElementById("upload_submission").disabled = false;
}