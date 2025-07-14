// Get references to key UI elements
const loginText = document.querySelector(".title-text .login");
const loginForm = document.querySelector("form.login");
const loginBtn = document.querySelector("label.login");
const signupBtn = document.querySelector("label.signup");
const signupLink = document.querySelector("form .signup-link a");
const signupForm = document.querySelector("form.signup");

// Handle switching to the signup form
signupBtn.onclick = () => {
    loginForm.style.marginLeft = "-50%";  
    loginText.style.marginLeft = "-50%";  
};
// Handle switching back to the login form
loginBtn.onclick = () => {
    loginForm.style.marginLeft = "0%";    
    loginText.style.marginLeft = "0%";    
};
// Clicking "Signup now" inside login form triggers the signup tab
signupLink.onclick = () => {
    signupBtn.click();                   
    return false;                         
};


// Handle Login form submission
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();  

    // Get user input values from login form
    const email = loginForm.querySelector("input[placeholder='Email Address']").value;
    const password = loginForm.querySelector("input[placeholder='Password']").value;

    try {
        // Send login credentials to backend
        const response = await fetch("/api/token/login/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Login successful: store auth token and redirect to homepage
            alert("Login successful!");
            localStorage.setItem("authToken", data.auth_token);
            window.location.href = "/";  // Redirect to index/home page
        } else {
            // Login failed: show error message from backend
            alert("Login failed: " + (data.non_field_errors || "Unknown error"));
        }
    } catch (err) {
        alert("Error during login: " + err.message);
    }
});

// Handle Signup form submission
signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();  

    // Extract user input from signup form
    const email = signupForm.querySelector("input[placeholder='Email Address']").value;
    const password = signupForm.querySelector("input[placeholder='Password']").value;
    const re_password = signupForm.querySelector("input[placeholder='Confirm password']").value;

    // Check if passwords match
    if (password !== re_password) {
        alert("Passwords do not match.");
        return;
    }

    try {
        // Send signup data to backend
        const response = await fetch("/api/users/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, re_password })
        });

        const data = await response.json();

        if (response.ok) {
            // Signup successful: inform user and switch to login form
            alert("Signup successful! Please login.");
            document.querySelector("label.login").click(); // Auto-switch to login tab
        } else {
            // Signup failed: display backend errors
            alert("Signup failed: " + JSON.stringify(data));
        }
    } catch (err) {
        alert("Error during signup: " + err.message);
    }
});
