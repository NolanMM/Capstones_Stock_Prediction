const loginText = document.querySelector(".title-text .login");
const loginForm = document.querySelector("form.login");
const loginBtn = document.querySelector("label.login");
const signupBtn = document.querySelector("label.signup");
const signupLink = document.querySelector("form .signup-link a");
signupBtn.onclick = (()=>{
        loginForm.style.marginLeft = "-50%";
        loginText.style.marginLeft = "-50%";
    });
    loginBtn.onclick = (() => {
        loginForm.style.marginLeft = "0%";
        loginText.style.marginLeft = "0%";
    });
    signupLink.onclick = (() => {
        signupBtn.click();
        return false;
    });


loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = loginForm.querySelector("input[placeholder='Email Address']").value;
    const password = loginForm.querySelector("input[placeholder='Password']").value;

    const response = await fetch("/api/token/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (response.ok) {
        alert("Login successful!");
        localStorage.setItem("authToken", data.auth_token);
        window.location.href = "/"; // or your home route
    } else {
        alert("Login failed: " + (data.non_field_errors || "Unknown error"));
    }
});

signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = signupForm.querySelector("input[placeholder='Email Address']").value;
    const password = signupForm.querySelector("input[placeholder='Password']").value;
    const re_password = signupForm.querySelector("input[placeholder='Confirm password']").value;

    if (password !== re_password) {
        alert("Passwords do not match.");
        return;
    }

    const response = await fetch("/api/users/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, re_password })
    });

    const data = await response.json();

    if (response.ok) {
        alert("Signup successful! Please login.");
        document.querySelector("label.login").click(); // switch to login tab
    } else {
        alert("Signup failed: " + JSON.stringify(data));
    }
});