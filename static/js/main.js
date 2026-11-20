// main.js - code shared by every page except the login page.

// 1. Talk to the server.
//    method is "GET", "POST" or "PUT". body is an object, or nothing.
async function callApi(method, url, body) {
    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "DukaTrack"
        }
    };
    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    const data = await response.json().catch(function () { return {}; });

    // 401 means not logged in, or the 15 minutes of idle time ran out
    if (response.status === 401 && document.body.id !== "login-page") {
        window.location = "login.html?ended=1";
        throw new Error("session");
    }
    if (!response.ok) {
        throw new Error(data.error || "Something went wrong.");
    }
    return data;
}

// 2. Show a message under a form. Red if bad is true.
function showMessage(element, text, bad) {
    element.textContent = text;
    if (bad) {
        element.classList.add("bad");
    } else {
        element.classList.remove("bad");
    }
}

// 3. Small helpers
function ksh(amount) {
    return "Ksh " + Number(amount).toLocaleString("en-KE");
}

function showError(element, error) {
    if (error.message !== "session") {
        showMessage(element, error.message, true);
    }
}

// A small coloured label (badge). kind is "ok", "warn", "low" or "off".
function makeBadge(text, kind) {
    const badge = document.createElement("span");
    badge.textContent = text;
    badge.className = "badge " + kind;
    return badge;
}

// Make one table row from a list of values. Numbers line up on the right.
function makeRow(values) {
    const row = document.createElement("tr");
    for (const value of values) {
        const cell = document.createElement("td");
        cell.textContent = value;
        if (typeof value === "number") {
            cell.className = "num";
        }
        row.appendChild(cell);
    }
    return row;
}

// Fill a drop-down list with products. firstText is the first, empty choice.
async function fillProducts(select, firstText) {
    const products = await callApi("GET", "/api/products");
    select.innerHTML = "";
    select.add(new Option(firstText, ""));
    for (const p of products) {
        select.add(new Option(p.name, p.id));
    }
    return products;
}

// 4. Start a page: find out who is logged in, then run the page's own code.
async function startPage(pageCode) {
    let user;
    try {
        user = await callApi("GET", "/api/me");
    } catch (error) {
        return;                    // callApi has already sent us to the login page
    }

    // show who is logged in
    document.querySelector("#who-name").textContent = user.name;
    document.querySelector("#who-role").textContent = "Shop " + user.role;
    document.querySelector("#who-role").className = "pill " + user.role;

    // hide what this role must not use (the server checks the role again)
    if (user.role === "Attendant") {
        for (const item of document.querySelectorAll(".owner-only")) {
            item.hidden = true;
        }
        if (document.body.dataset.role === "Owner") {
            window.location = "stock.html";
            return;
        }
    } else {
        for (const item of document.querySelectorAll(".attendant-only")) {
            item.hidden = true;
        }
    }

    // mark the page we are on in the nav bar
    for (const link of document.querySelectorAll("nav a")) {
        if (link.getAttribute("href") === location.pathname.split("/").pop()) {
            link.classList.add("current");
        }
    }

    pageCode(user);
}

// 5. Log out button (FR05, FR06)
const logoutButton = document.querySelector("#logout");
if (logoutButton) {
    logoutButton.addEventListener("click", async function () {
        try {
            await callApi("POST", "/api/logout");
        } catch (error) {
            // already logged out
        }
        window.location = "login.html?out=1";
    });
}
