// Enable/disable mock mode for testing without backend
const debugMode = false;

// Use the auth manager to check authentication
if (!authManager.requireAuth()) {
    // requireAuth will handle the redirect if not logged in
    throw new Error('Authentication required');
}

// Setup request headers for session-based authentication (no token needed)
const headers = {
    "Content-Type": "application/json"
};

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
    fetch('/api/account/', { // Correct endpoint
            method: "GET",
            headers,
            credentials: 'include' // Include session cookies
        })
        .then(response => {
            if (!response.ok) throw new Error("Unauthorized");
            return response.json();
        })
        .then(data => {
            // Populate account UI with fetched data
            document.getElementById('email-display').textContent = data.email;
            document.getElementById('password-display').textContent = '********'; // Masked password
            if (data.profile && data.profile.profile_picture_url) {
                document.getElementById('profile-image').src = data.profile.profile_picture_url;
            } else {
                document.getElementById('profile-image').src = './static/images/profile-picture-placeholder.jpg';
            }
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
    // Hide the "Change Email" button itself
    document.getElementById('button-edit-email').classList.add('d-none');
}

// Confirm new email and send update to server
function confirmEmail() {
    const newEmail = document.getElementById('email-input').value;
    if (!newEmail) return alert("Please enter a valid email.");

    // In debug mode, just update UI
    if (debugMode) {
        document.getElementById('email-display').textContent = newEmail;
        cancelEmail();
        return;
    }

    fetch('/api/account/', { // Correct endpoint
            method: "PUT",
            headers,
            credentials: 'include',
            body: JSON.stringify({
                email: newEmail
            })
        })
        .then(res => {
            if (!res.ok) throw new Error("Failed to update email.");
            return res.json();
        })
        .then(() => {
            document.getElementById('email-display').textContent = newEmail;
            cancelEmail(); // Hide input field
            alert("Email updated successfully!"); // User feedback
        })
        .catch(err => {
            console.error('Error updating email:', err);
            alert("Failed to update email.");
        });
}

// Cancel email editing and restore display
function cancelEmail() {
    document.getElementById('email-input-container').classList.add('d-none');
    document.getElementById('email-display').classList.remove('d-none');
    // Show the "Change Email" button again
    document.getElementById('button-edit-email').classList.remove('d-none');
}

// === Password Handling ===

// Show password input field to allow editing
function editPassword() {
    document.getElementById('password-display').classList.add('d-none');
    document.getElementById('password-input-container').classList.remove('d-none');
    // Hide the "Change Password" button itself
    document.getElementById('button-edit-password').classList.add('d-none');
}

// Confirm new password and send update to server
function confirmPassword() {
    const newPassword = document.getElementById('password-input').value;
    if (!newPassword) return alert("Please enter a valid password.");

    // In debug mode, just update UI
    if (debugMode) {
        document.getElementById('password-display').textContent = '*'.repeat(newPassword.length);
        cancelPassword();
        return;
    }

    fetch('/api/account/', { // Correct endpoint
            method: "PUT",
            headers,
            credentials: 'include',
            body: JSON.stringify({
                password: newPassword
            })
        })
        .then(res => {
            if (!res.ok) throw new Error("Failed to update password.");
            return res.json();
        })
        .then(() => {
            // Mask password and hide input
            document.getElementById('password-display').textContent = '*'.repeat(newPassword.length);
            cancelPassword();
            alert("Password updated successfully!"); // User feedback
        })
        .catch(err => {
            console.error('Error updating password:', err);
            alert("Failed to update password.");
        });
}

// Cancel password editing and restore masked password
function cancelPassword() {
    document.getElementById('password-input-container').classList.add('d-none');
    document.getElementById('password-display').classList.remove('d-none');
    // Show the "Change Password" button again
    document.getElementById('button-edit-password').classList.remove('d-none');
}

// === Profile Picture Handling ===

// Start profile picture change by showing URL input
function changeProfilePicture() {
    document.getElementById('profile-image').classList.add('d-none'); // Hide image
    document.getElementById('button-change-profile-picture').classList.add('d-none'); // Hide initial button
    document.getElementById('url-input-container').classList.remove('d-none'); // Show input field
}

// Confirm and send profile picture URL update to server
function changeImageUrl() {
    const imageUrl = document.getElementById('image-url-input').value;
    if (!imageUrl) return alert("Please enter a valid image URL.");

    // In debug mode, just update UI
    if (debugMode) {
        document.getElementById('profile-image').src = imageUrl;
        cancelChange();
        return;
    }

    fetch('/api/account/', { // Correct endpoint
            method: "PUT",
            headers,
            credentials: 'include',
            body: JSON.stringify({
                profile: {
                    profile_picture_url: imageUrl
                }
            })
        })
        .then(res => {
            if (!res.ok) throw new Error("Failed to update profile picture.");
            return res.json();
        })
        .then(() => {
            // Update UI with new profile picture
            document.getElementById('profile-image').src = imageUrl;
            cancelChange(); // Hide input field
            alert("Profile picture updated successfully!"); // User feedback
        })
        .catch(err => {
            console.error('Error updating profile picture:', err);
            alert("Failed to update profile picture.");
        });
}

// Cancel profile picture change
function cancelChange() {
    document.getElementById('profile-image').classList.remove('d-none'); // Show image
    document.getElementById('button-change-profile-picture').classList.remove('d-none'); // Show initial button
    document.getElementById('url-input-container').classList.add('d-none'); // Hide input field
    document.getElementById('image-url-input').value = ''; // Clear input
}

// === Auth Actions ===

// Logout: use auth manager to properly clear session
document.getElementById("button-log-out").onclick = () => {
    authManager.logout();
};

// Delete Account: confirm and send delete request
document.getElementById("button-delete-account").onclick = () => {
    if (!confirm("Are you sure you want to delete your account? This action cannot be undone.")) return;

    // In debug mode, just show alert
    if (debugMode) {
        alert("Account deleted successfully (simulated).");
        localStorage.removeItem("authToken");
        window.location.href = "/register.html";
        return;
    }

    fetch('/api/account/', { // Correct endpoint
            method: "DELETE",
            headers,
            credentials: 'include'
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
        .catch(err => {
            console.error('Error deleting account:', err);
            alert("An error occurred while deleting account.");
        });
};