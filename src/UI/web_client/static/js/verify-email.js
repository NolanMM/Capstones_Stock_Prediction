document.addEventListener("DOMContentLoaded", () => {
    const verifyForm = document.getElementById("verify-form");
    const otpInput = document.getElementById("otp-input");

    verifyForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const otp = otpInput.value;
        const urlParams = new URLSearchParams(window.location.search);
        const email = urlParams.get('email');

        if (!otp || !email) {
            alert("OTP and email are required for verification.");
            return;
        }

        try {
            const response = await fetch("/api/verify-email/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, otp })
            });

            const contentType = response.headers.get("content-type");

            // Check if the response is JSON
            if (contentType && contentType.includes("application/json")) {
                const data = await response.json();
                if (response.ok) {
                    alert("Email verified successfully! You can now log in.");
                    window.location.href = "/register.html";
                } else {
                    alert("Verification failed: " + (data.error || "Unknown error."));
                }
            } else {
                // If not JSON, it's an HTML error page from the server
                console.error("Server did not return JSON. This is likely a server configuration issue (e.g., CSRF error).");
                alert("Verification failed: The server returned an unexpected response. Please try again later.");
            }
        } catch (err) {
            alert("A network error occurred during verification: " + err.message);
        }
    });
});