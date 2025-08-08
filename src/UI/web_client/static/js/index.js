document.addEventListener("DOMContentLoaded", function () {
    // === Debug Mode Flag ===
    const debugMode = true;

    // === Auth Token Setup ===
    const token = localStorage.getItem("authToken");

    const contactForm = document.querySelector(".contact-form");

    if (contactForm) {
        contactForm.addEventListener("submit", function(event) {
            event.preventDefault();

            const name = document.getElementById("contactName").value;
            const phone = document.getElementById("contactPhone").value;
            const email = document.getElementById("contactEmail").value;
            const subject = document.getElementById("contactSubject").value;
            const message = document.getElementById("contactMessage").value;
            
            if (!name.trim() || !message.trim()) {
                alert("Please fill out your name and message.");
                return;
            }

            const formData = {
                user_name: name,
                phone_number: phone,
                user_email: email,
                email_subject: subject,
                message_text: message
            };

            fetch('/api/contact-submit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    alert("Success! " + data.message);
                    contactForm.reset();
                } else {
                    let errorText = "Please correct the following errors:\n";
                    for (const field in data) {
                        errorText += `${field}: ${data[field].join(', ')}\n`;
                    }
                    alert(errorText);
                }
            })
            .catch(error => {
                console.error('Error submitting form:', error);
                alert("An error occurred while submitting your message. Please try again later.");
            });
        });
    }

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
