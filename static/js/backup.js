// backup.js - back up data (FR16, Owner)
const backupButton = document.querySelector("#backup-button");
const backupMessage = document.querySelector("#backup-message");
const backupBody = document.querySelector("#backup-body");

startPage(loadBackups);

async function loadBackups() {
    try {
        const logs = await callApi("GET", "/api/backups");
        backupBody.innerHTML = "";
        for (const b of logs) {
            const row = makeRow([b.date.replace("T", " "), b.by, b.file || "-"]);
            const status = document.createElement("td");
            status.appendChild(makeBadge(b.status, b.status === "Success" ? "ok" : "low"));
            row.appendChild(status);
            backupBody.appendChild(row);
        }
    } catch (error) {
        showError(backupMessage, error);
    }
}

backupButton.addEventListener("click", async function () {
    backupButton.disabled = true;
    try {
        await callApi("POST", "/api/backups");
        showMessage(backupMessage, "Backup saved.", false);
    } catch (error) {
        showError(backupMessage, error);
    }
    backupButton.disabled = false;
    loadBackups();
});
