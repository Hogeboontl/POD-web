{
    var ram_input = document.getElementById("ram_input")
    const ram_MAX = Number(ram_input.dataset.ramMax);

    var valid_nums = true;

    ram_input.addEventListener("input", () => {
        const val = Number(ram_input.value);
        
        if (val < 1) {
            ram_input.style.outline = "2px solid red";
            document.getElementById("error-text").textContent = "value must be greater than 1"
            valid_nums = false;
        }
        else if (val > ram_MAX ) {
            ram_input.style.outline = "2px solid red";
            document.getElementById("error-text").textContent = `value must be less than ${ram_MAX}`
            valid_nums = false;
        }
        else {
            ram_input.style.outline = "";
            document.getElementById("error-text").textContent = ""
            valid_nums = true;
        }
    });

    document.getElementById("save").addEventListener("click", () => {
        if (valid_nums == true) {
            fetch('/adjust_server_settings', {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({"mem": ram_input.value,
                                      "cores": document.getElementById("core-selection").value})
            })
            .then(() =>{
                window.close()
            }
    
            );
        }
        
    });
}