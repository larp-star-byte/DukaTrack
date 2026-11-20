// reports.js - sales report (FR22), CSV export (FR23), forecast accuracy (FR24)
const reportPeriod = document.querySelector("#report-period");
const csvLink = document.querySelector("#csv-link");
const reportTitle = document.querySelector("#report-title");
const reportBody = document.querySelector("#report-body");
const totalUnits = document.querySelector("#total-units");
const totalRevenue = document.querySelector("#total-revenue");
const accuracyBody = document.querySelector("#accuracy-body");
const reportMessage = document.querySelector("#report-message");

startPage(function () {
    loadReport();
    loadAccuracy();
});

async function loadReport() {
    try {
        const report = await callApi("GET", "/api/reports/sales?period=" + reportPeriod.value);
        csvLink.href = "/api/reports/sales.csv?period=" + reportPeriod.value;
        reportTitle.textContent = "Sales report: " + report.from + " to " + report.to;
        reportBody.innerHTML = "";
        for (const r of report.rows) {
            reportBody.appendChild(makeRow([r.product, r.units, ksh(r.revenue)]));
            reportBody.lastChild.children[2].className = "num";
        }
        totalUnits.textContent = report.total_units;
        totalRevenue.textContent = ksh(report.total_revenue);
        showMessage(reportMessage, report.rows.length === 0 ? "No sales in this period." : "", false);
    } catch (error) {
        showError(reportMessage, error);
    }
}

async function loadAccuracy() {
    try {
        const accuracy = await callApi("GET", "/api/reports/accuracy");
        accuracyBody.innerHTML = "";
        for (const r of accuracy.rows) {
            accuracyBody.appendChild(makeRow([r.product, r.forecasts, r.predicted, r.actual, r.mae]));
        }
    } catch (error) {
        showError(reportMessage, error);
    }
}

reportPeriod.addEventListener("change", loadReport);
