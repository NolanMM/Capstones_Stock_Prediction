// Authentication helper functions for the frontend
class AuthManager {
    constructor() {
        this.userInfo = null;
        this.loadUserInfo();
    }

    // Load user info from localStorage
    loadUserInfo() {
        const stored = localStorage.getItem('userInfo');
        if (stored) {
            try {
                this.userInfo = JSON.parse(stored);
            } catch (e) {
                console.error('Failed to parse user info:', e);
                this.clearAuth();
            }
        }
    }

    // Check if user is logged in
    isLoggedIn() {
        return this.userInfo !== null;
    }

    // Get current user info
    getCurrentUser() {
        return this.userInfo;
    }

    // Set user info after login
    setUserInfo(userInfo) {
        this.userInfo = userInfo;
        localStorage.setItem('userInfo', JSON.stringify(userInfo));
        this.updateNavigation();
    }

    // Clear authentication data
    clearAuth() {
        this.userInfo = null;
        localStorage.removeItem('userInfo');
        localStorage.removeItem('authToken'); // Remove old token if it exists
        this.updateNavigation();
    }

    // Update navigation based on auth state
    updateNavigation() {
        const accountLink = document.querySelector('a[href="account.html"]');
        if (accountLink) {
            if (this.isLoggedIn()) {
                accountLink.textContent = 'Account';
                accountLink.href = 'account.html';
            } else {
                accountLink.textContent = 'Sign In';
                accountLink.href = 'register.html';
            }
        }
    }

    // Logout and redirect
    async logout() {
        try {
            // Try to call logout endpoint (but don't worry if it fails due to CSRF)
            await fetch('/api/logout/', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
        } catch (e) {
            console.log('Logout endpoint failed, but clearing local auth anyway');
        }
        
        this.clearAuth();
        window.location.href = '/index.html';
    }

    // Require authentication for protected pages
    requireAuth(redirectUrl = '/register.html') {
        if (!this.isLoggedIn()) {
            alert('Please log in to access this page.');
            window.location.href = redirectUrl;
            return false;
        }
        return true;
    }
}

// Create global auth manager instance
window.authManager = new AuthManager();

// Initialize navigation on page load
document.addEventListener('DOMContentLoaded', function() {
    window.authManager.updateNavigation();
    
    // Add logout functionality if user is logged in
    if (window.authManager.isLoggedIn()) {
        // Add logout option to account dropdown or similar
        // This can be enhanced based on your UI design
    }
});
