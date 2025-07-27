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
    const first_name = signupForm.querySelector("input[placeholder='First Name']").value;
    const last_name = signupForm.querySelector("input[placeholder='Last Name']").value;
    const email = signupForm.querySelector("input[placeholder='Email Address']").value;
    const password = signupForm.querySelector("input[placeholder='Password']").value;
    const re_password = signupForm.querySelector("input[placeholder='Confirm password']").value;
    const username = email.split('@')[0];

    console.log("Signup data:", { first_name, last_name, email, password, re_password });

    // Check if any required fields are empty
    if (!username || !email || !password || !re_password || !first_name || !last_name) {
        alert("All fields are required. Email must contain '@' and password must be at least 8 characters long.");
        return;
    }

    if (password !== re_password) {
        alert("Passwords do not match.");
        return;
    }

    try {
        const response = await fetch("/api/register/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, first_name, last_name, password, re_password })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Registration successful! Please check your email for a verification code.");
            window.location.href = `/verify-email-page/?email=${encodeURIComponent(email)}`;
        } else {
            let errorMessage = "Signup failed: ";
            if (data.username) {
                errorMessage += "This username (email) is already taken.";
            } else if (data.email) {
                errorMessage += "This email is already registered.";
            } else if (data.re_password) {
                errorMessage += "Password confirmation failed: " + data.re_password[0];
            }
             else {
                errorMessage += JSON.stringify(data);
            }
            alert(errorMessage);
        }
    } catch (err) {
        alert("Error during signup: " + err.message);
    }
});
