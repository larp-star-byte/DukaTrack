// attendants.js - create attendant account (FR03) and deactivate it (FR04)
const attendantForm = document.querySelector("#attendant-form");
const attName = document.querySelector("#att-name");
const attPhone = document.querySelector("#att-phone");
const attUsername = document.querySelector("#att-username");
const attPassword = document.querySelector("#att-password");
const attMessage = document.querySelector("#att-message");
const attendantsBody = document.querySelector("#attendants-body");
const listMessage = document.querySelector("#list-message");

startPage(loadAttendants);

async function loadAttendants() {
    try {
        const list = await callApi("GET", "/api/attendants");
        attendantsBody.innerHTML = "";
        for (const u of list) {
            const row = makeRow([u.name, u.phone || "", u.username]);
            const status = document.createElement("td");
            status.appendChild(makeBadge(u.active ? "Active" : "Inactive", u.active ? "ok" : "off"));
            row.appendChild(status);

            const action = document.createElement("td");
            if (u.active) {
                const off = document.createElement("button");
                off.textContent = "Deactivate";
                off.className = "small danger";
                off.addEventListener("click", function () { deactivate(u.id); });
                action.appendChild(off);
            }
            row.appendChild(action);
            attendantsBody.appendChild(row);
        }
    } catch (error) {
        showError(listMessage, error);
    }
}

attendantForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    try {
        await callApi("POST", "/api/attendants", {
            name: attName.value,
            phone: attPhone.value,
            username: attUsername.value,
            password: attPassword.value
        });
        showMessage(attMessage, "Account created.", false);
        attendantForm.reset();
        loadAttendants();
    } catch (error) {
        showError(attMessage, error);
    }
});

async function deactivate(id) {
    if (!confirm("Deactivate this attendant account?")) {
        return;
    }
    try {
        await callApi("POST", "/api/attendants/" + id + "/deactivate");
        showMessage(listMessage, "Account deactivated.", false);
        loadAttendants();
    } catch (error) {
        showError(listMessage, error);
    }
}
