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
        // Send login credentials to backend using our custom session-based login
        const response = await fetch("/api/login/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Login successful: use auth manager to store user info
            alert("Login successful!");
            authManager.setUserInfo(data.user);
            window.location.href = "/";  // Redirect to index/home page
        } else {
            // Login failed: show error message from backend
            alert("Login failed: " + (data.error || "Unknown error"));
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
    const username = signupForm.querySelector("input[placeholder='Username']").value;
    const password = signupForm.querySelector("input[placeholder='Password']").value;
    const re_password = signupForm.querySelector("input[placeholder='Confirm password']").value;

    // Debug: Log the values to console
    console.log("Signup data:", { username, email, password, re_password });
    
    // Check if any required fields are empty
    if (!username || !email || !password || !re_password) {
        alert("All fields are required.");
        return;
    }

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
            body: JSON.stringify({ username, email, password, re_password })
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
