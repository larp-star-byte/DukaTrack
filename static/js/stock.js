// stock.js - stock levels (FR19, FR20) and low-stock list (FR21)
const stockBody = document.querySelector("#stock-body");
const lowBody = document.querySelector("#low-body");
const stockMessage = document.querySelector("#stock-message");

startPage(loadStock);

async function loadStock(user) {
    try {
        const stock = await callApi("GET", "/api/stock");
        stockBody.innerHTML = "";
        for (const p of stock) {
            const row = makeRow([p.name, p.category, p.stock, p.reorder_level]);
            const status = document.createElement("td");
            if (p.stock === 0) {
                status.appendChild(makeBadge("Out of stock", "low"));
            } else if (p.low) {
                status.appendChild(makeBadge("Low", "warn"));
            } else {
                status.appendChild(makeBadge("OK", "ok"));
            }
            row.appendChild(status);
            stockBody.appendChild(row);
        }

        // only the Owner sees the low-stock list
        if (user.role === "Owner") {
            const low = await callApi("GET", "/api/stock/low");
            lowBody.innerHTML = "";
            for (const p of low) {
                lowBody.appendChild(makeRow([p.name, p.stock, p.reorder_level]));
            }
            // a coloured banner above the table
            if (low.length === 0) {
                stockMessage.textContent = "No product is below its reorder level.";
                stockMessage.className = "banner";
            } else {
                const names = low.map(function (p) { return p.name; });
                stockMessage.textContent = low.length + " product(s) at or below the reorder level: " + names.join(", ");
                stockMessage.className = "banner bad";
            }
        }
    } catch (error) {
        showError(stockMessage, error);
    }
}
