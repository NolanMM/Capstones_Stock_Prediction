document.addEventListener("DOMContentLoaded", function () {
    // === Debug Mode Flag ===
    const debugMode = true;

    // === Auth Token Setup ===
    const token = localStorage.getItem("authToken");

    // Setup headers for API requests
    const headers = {
        "Content-Type": "application/json",
        "Authorization": `Token ${token}`
    };

    // === Auth Check (forced if debugMode is true) ===
    const userIsLoggedIn = debugMode ? true : !!token;

    // === UI Logic Based on Login State ===
    const portfolioLink = document.querySelector('.nav-link[href="portfolio.html"]');
    const accountLink = document.querySelector('.nav-link[href="account.html"]');

    if (userIsLoggedIn) {
        document.getElementById("signinCard").style.display = "none";
        document.getElementById("portfolioCard").style.display = "block";

        if (portfolioLink) {
            portfolioLink.style.display = 'block';
        }

        if (accountLink) {
            accountLink.setAttribute('href', 'account.html');
        }
    } else {
        document.getElementById("signinCard").style.display = "block";
        document.getElementById("portfolioCard").style.display = "none";

        if (portfolioLink) {
            portfolioLink.style.display = 'none';
        }

        if (accountLink) {
            accountLink.setAttribute('href', 'register.html');
        }
    }
});
