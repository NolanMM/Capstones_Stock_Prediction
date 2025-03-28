// Fetch account data from the JSON stub
fetch('./static/json/account.json')
    .then(response => response.json())
    .then(data => {
        // Populate email, password (masked), and profile picture
        document.getElementById('email-display').textContent = data.email;

         // Generate a string of stars (*) with the same length as the password
        var maskedPassword = '*'.repeat(data.password.length);
        document.getElementById('password-display').textContent = maskedPassword;
        document.getElementById('profile-image').src = data.profilePicture;
    })
    .catch(error => {
        console.error('Error fetching account data:', error);
    });

// Function to start editing email
function editEmail() {
    document.getElementById('email-display').classList.add('d-none');
    document.getElementById('email-input-container').classList.remove('d-none');
}

// Function to start editing password
function editPassword() {
    document.getElementById('password-display').classList.add('d-none');
    document.getElementById('password-input-container').classList.remove('d-none');
}

// Function to confirm email change
function confirmEmail() {
    var newEmail = document.getElementById('email-input').value;
    if (newEmail) {
        // Update the email on the screen
        document.getElementById('email-display').textContent = newEmail;
        // Hide the input field and show the new email
        document.getElementById('email-input-container').classList.add('d-none');
        document.getElementById('email-display').classList.remove('d-none');
        
        // Optionally, update the email in the JSON or make an API call here
        console.log("New email:", newEmail); // Example of what you might do
    } else {
        alert("Please enter a valid email.");
    }
}

// Function to confirm password change
function confirmPassword() {
    var newPassword = document.getElementById('password-input').value;
    if (newPassword) {
        // Generate a string of stars (*) with the same length as the password
        var maskedPassword = '*'.repeat(newPassword.length);

        // Update the password on the screen with the masked password
        document.getElementById('password-display').textContent = maskedPassword;
        
        // Hide the input field and show the masked password
        document.getElementById('password-input-container').classList.add('d-none');
        document.getElementById('password-display').classList.remove('d-none');
        
        // Optionally, update the password in the JSON or make an API call here
        console.log("New password:", newPassword); // Example of what you might do
    } else {
        alert("Please enter a valid password.");
    }
}


// Function to change the profile picture
function changeProfilePicture() {
    // Hide the profile image and change profile button
    document.getElementById('profile-image').style.display = 'none';
    document.getElementById('change-profile-container').style.display = 'none'; 
    // Show the input field for the new image URL
    document.getElementById('url-input-container').classList.remove('d-none'); 
}

// Function to confirm and change the profile image to the new URL
function changeImageUrl() {
    var imageUrl = document.getElementById('image-url-input').value;
    if (imageUrl) {
    // Change the profile image to the new URL
    document.getElementById('profile-image').src = imageUrl;
    // Show the new image
    document.getElementById('profile-image').style.display = 'block';
    // Hide the input field and buttons again
    document.getElementById('url-input-container').classList.add('d-none');
    // Show the "Change Profile Picture" button again
    document.getElementById('change-profile-container').style.display = 'block';
    } else {
        alert("Please enter a valid image URL.");
    }
}

// Function to cancel the image change
function cancelChange() {
    // Restore the profile image and change button
    document.getElementById('profile-image').style.display = 'block';
    document.getElementById('change-profile-container').style.display = 'block';
    // Hide the URL input field and buttons
    document.getElementById('url-input-container').classList.add('d-none');
}

// Function to cancel email change and restore the email display
function cancelEmail() {
    // Hide the input field and show the current email display
    document.getElementById('email-input-container').classList.add('d-none');
    document.getElementById('email-display').classList.remove('d-none');
}

// Function to cancel password change and restore the password display
function cancelPassword() {
    // Hide the input field and show the masked password display
    document.getElementById('password-input-container').classList.add('d-none');
    document.getElementById('password-display').classList.remove('d-none');
}