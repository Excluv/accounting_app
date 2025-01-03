document.addEventListener("DOMContentLoaded", function() {
    const addButton = document.querySelector(".add-row");
    if (addButton) {
        addButton.addEventListener("click", function() {
            const lastRow = document.querySelector(".dynamic-transaction_set:last-child");
            if (lastRow) {
                const clone = lastRow.cloneNode(true);
                const inputs = clone.querySelectorAll("input", "select");
                inputs.forEach(input => {
                    input.value = "";
                    const name = input.name.replace(/-\d+-/, `-${inputs.length}-`);
                    input.name = name;
                    input.id = name;
                });
                lastRow.after(clone);
            }
        });
    }
});