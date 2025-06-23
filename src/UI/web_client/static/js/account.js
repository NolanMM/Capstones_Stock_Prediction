// Get auth token from local storage
const token = localStorage.getItem("authToken");

// Redirect to login if token is missing
if (!token) {
    alert("Please log in to access your account.");
    window.location.href = "/register.html";
}

// Setup request headers with token for authentication
const headers = {
    "Content-Type": "application/json",
    "Authorization": `Token ${token}`
};

// Enable/disable mock mode for testing without backend
const debugMode = true;

if (debugMode) {
    // Simulated account data for testing UI without backend
    const mockData = {
        email: "mockuser@example.com",
        profilePicture: "./static/images/profile-picture-placeholder.jpg"
    };

    // Populate UI with mock data
    document.getElementById('email-display').textContent = mockData.email;
    document.getElementById('password-display').textContent = '********';
    document.getElementById('profile-image').src = mockData.profilePicture;
} else {
    // Fetch real account data from Django API
    fetch('/api/account/', { // Update end point to match your API
        method: "GET",
        headers
    })
        .then(response => {
            if (!response.ok) throw new Error("Unauthorized");
            return response.json();
        })
        .then(data => {
            // Populate account UI with fetched data
            document.getElementById('email-display').textContent = data.email;
            document.getElementById('password-display').textContent = '********'; // Masked password
            document.getElementById('profile-image').src = data.profilePicture;
        })
        .catch(error => {
            console.error('Error fetching account data:', error);
            alert("You must be logged in to access your account.");
            window.location.href = "/register.html";
        });
}

// === Email Handling ===

// Show email input field to allow editing
function editEmail() {
    document.getElementById('email-display').classList.add('d-none');
    document.getElementById('email-input-container').classList.remove('d-none');
}

// Confirm new email and send update to server
function confirmEmail() {
    const newEmail = document.getElementById('email-input').value;
    if (!newEmail) return alert("Please enter a valid email.");

    fetch('/api/account/', { // Update end point to match your API
        method: "PUT",
        headers,
        body: JSON.stringify({ email: newEmail })
    })
        .then(res => res.json())
        .then(() => {
            document.getElementById('email-display').textContent = newEmail;
            cancelEmail(); // Hide input field
        })
        .catch(err => alert("Failed to update email."));
}

// Cancel email editing and restore display
function cancelEmail() {
    document.getElementById('email-input-container').classList.add('d-none');
    document.getElementById('email-display').classList.remove('d-none');
}

// === Password Handling ===

// Show password input field to allow editing
function editPassword() {
    document.getElementById('password-display').classList.add('d-none');
    document.getElementById('password-input-container').classList.remove('d-none');
}

// Confirm new password and send update to server
function confirmPassword() {
    const newPassword = document.getElementById('password-input').value;
    if (!newPassword) return alert("Please enter a valid password.");

    fetch('/api/account/', { // Update end point to match your API
        method: "PUT",
        headers,
        body: JSON.stringify({ password: newPassword })
    })
        .then(res => res.json())
        .then(() => {
            // Mask password and hide input
            document.getElementById('password-display').textContent = '*'.repeat(newPassword.length);
            cancelPassword();
        })
        .catch(err => alert("Failed to update password."));
}

// Cancel password editing and restore masked password
function cancelPassword() {
    document.getElementById('password-input-container').classList.add('d-none');
    document.getElementById('password-display').classList.remove('d-none');
}

// === Profile Picture Handling ===

// Start profile picture change by showing URL input
function changeProfilePicture() {
    document.getElementById('profile-image').style.display = 'none';
    document.getElementById('change-profile-container').style.display = 'none';
    document.getElementById('url-input-container').classList.remove('d-none');
}

// Confirm and send profile picture URL update to server
function changeImageUrl() {
    const imageUrl = document.getElementById('image-url-input').value;
    if (!imageUrl) return alert("Please enter a valid image URL.");

    fetch('/api/account/', { // Update end point to match your API
        method: "PUT",
        headers,
        body: JSON.stringify({ profilePicture: imageUrl })
    })
        .then(res => res.json())
        .then(() => {
            // Update UI with new profile picture
            document.getElementById('profile-image').src = imageUrl;
            document.getElementById('profile-image').style.display = 'block';
            document.getElementById('url-input-container').classList.add('d-none');
            document.getElementById('change-profile-container').style.display = 'block';
        })
        .catch(err => alert("Failed to update profile picture."));
}

// Cancel profile picture change
function cancelChange() {
    document.getElementById('profile-image').style.display = 'block';
    document.getElementById('change-profile-container').style.display = 'block';
    document.getElementById('url-input-container').classList.add('d-none');
}

// === Auth Actions ===

// Logout: remove auth token and redirect to login
document.getElementById("button-log-out").onclick = () => {
    localStorage.removeItem("authToken");
    window.location.href = "/register.html";
};

// Delete Account: confirm and send delete request
document.getElementById("button-delete-account").onclick = () => {
    if (!confirm("Are you sure you want to delete your account? This action cannot be undone.")) return;

    fetch('/api/account/', { // Update end point to match your API
        method: "DELETE",
        headers
    })
    .then(response => {
        if (response.ok) {
            alert("Account deleted successfully.");
            localStorage.removeItem("authToken");
            window.location.href = "/register.html";
        } else {
            alert("Failed to delete account.");
        }
    })
    .catch(err => alert("An error occurred while deleting account."));
};
