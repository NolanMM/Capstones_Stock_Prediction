document.addEventListener("DOMContentLoaded", function () {
    const portfolioLink = document.querySelector('.nav-link[href="portfolio.html"]');
    const accountLink = document.querySelector('.nav-link[href="account.html"]');
    
    // Simulated check for login status, replace with your actual check
    function isLoggedIn() {
        // This is a placeholder. Replace it with your actual login check.
        return true; // Assuming the user is not logged in for this example
    }

    // Check if user is logged in
    const userIsLoggedIn = isLoggedIn();

    // Display elements based on login status
    if (userIsLoggedIn) {
        document.getElementById("signinCard").style.display = "none";
        document.getElementById("portfolioCard").style.display = "block";
        if (portfolioLink) {
            portfolioLink.style.display = 'block'; // Ensure portfolio link is visible
        }
        if (accountLink) {
            accountLink.setAttribute('href', 'account.html'); // Ensure "Account" button links to account page
        }
    } else {
        document.getElementById("signinCard").style.display = "block";
        document.getElementById("portfolioCard").style.display = "none";
        if (portfolioLink) {
            portfolioLink.style.display = 'none'; // Hide "Your Portfolio" link
        }
        if (accountLink) {
            accountLink.setAttribute('href', 'register.html'); // Change "Account" button to register page
        }
    }
});
