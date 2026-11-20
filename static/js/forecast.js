// forecast.js - generate a forecast (FR15), view it (FR17 Owner, FR18 Attendant)
const periodSelect = document.querySelector("#period");
const productSelect = document.querySelector("#product");
const runButton = document.querySelector("#run");
const forecastBody = document.querySelector("#forecast-body");
const forecastMessage = document.querySelector("#forecast-message");
const forecastNote = document.querySelector("#forecast-note");

startPage(async function (user) {
    if (user.role === "Owner") {
        await fillProducts(productSelect, "All products");
    }
    loadForecast();
});

// Draw a small line of the last 28 days of sales (an SVG picture).
// Each day becomes one point: x moves right, y goes up when more was sold.
function drawLine(days) {
    const width = 120;
    const height = 30;
    let biggest = 1;
    for (const d of days) {
        if (d > biggest) { biggest = d; }
    }
    const points = [];
    for (let i = 0; i < days.length; i++) {
        const x = i * width / (days.length - 1);
        const y = height - 2 - days[i] / biggest * (height - 4);
        points.push(x.toFixed(1) + "," + y.toFixed(1));
    }
    return '<svg class="spark" width="' + width + '" height="' + height + '"><polyline points="' +
        points.join(" ") + '" fill="none" stroke="#0f766e" stroke-width="1.8"/></svg>';
}

// show the latest saved forecast for the chosen period
async function loadForecast() {
    try {
        const rows = await callApi("GET", "/api/forecasts/latest?period_days=" + periodSelect.value);
        forecastBody.innerHTML = "";
        forecastNote.textContent = "";
        if (rows.length === 0) {
            showMessage(forecastMessage, "No forecast yet for this period.", true);
            return;
        }
        for (const r of rows) {
            const predicted = Math.round(r.predicted);
            const row = makeRow([r.product, "", predicted, r.stock]);
            const lineCell = row.children[1];
            lineCell.className = "hide-small";
            lineCell.innerHTML = drawLine(r.history);      // numbers only, so this is safe
            row.children[2].innerHTML = "<strong>" + predicted + "</strong>";

            const check = document.createElement("td");
            if (r.enough_stock) {
                check.appendChild(makeBadge("Enough stock", "ok"));
            } else {
                check.appendChild(makeBadge("Short by " + Math.max(0, Math.ceil(r.predicted - r.stock)), "low"));
            }
            row.appendChild(check);
            forecastBody.appendChild(row);
        }
        showMessage(forecastMessage, "", false);
        forecastNote.textContent = "Forecast made " + rows[0].generated_at.replace("T", " ") +
            " for " + rows[0].period_days + " days from " + rows[0].period_start + ".";
    } catch (error) {
        showError(forecastMessage, error);
    }
}

periodSelect.addEventListener("change", loadForecast);

// Owner presses Generate forecast
runButton.addEventListener("click", async function () {
    runButton.disabled = true;
    showMessage(forecastMessage, "Working...", false);
    try {
        const result = await callApi("POST", "/api/forecasts", {
            period_days: Number(periodSelect.value),
            product_id: productSelect.value || null
        });
        await loadForecast();
        showMessage(forecastMessage, "Forecast ready for " + result.products + " product(s).", false);
    } catch (error) {
        showError(forecastMessage, error);
    }
    runButton.disabled = false;
});
