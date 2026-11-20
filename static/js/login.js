// login.js - the login page (FR01 Owner, FR02 Attendant)
const loginForm = document.querySelector("#login-form");
const username = document.querySelector("#username");
const password = document.querySelector("#password");
const loginMessage = document.querySelector("#login-message");

// message when we were sent back here
if (location.search.includes("ended")) {
    showMessage(loginMessage, "Your session ended. Please log in again.", true);
} else if (location.search.includes("out")) {
    showMessage(loginMessage, "You have been logged out.", false);
}

loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();                    // stop the page from reloading
    try {
        const user = await callApi("POST", "/api/login", {
            username: username.value,
            password: password.value
        });
        // the Owner starts at stock levels, the Attendant at sales
        if (user.role === "Owner") {
            window.location = "stock.html";
        } else {
            window.location = "sales.html";
        }
    } catch (error) {
        password.value = "";
        showMessage(loginMessage, error.message, true);
    }
});
