// 🔥 Production Backend URL
const API_BASE = "https://my-logic.onrender.com/api";

document.addEventListener('DOMContentLoaded', () => {
    // Redirect if already logged in
    if (localStorage.getItem('token')) {
        window.location.href = 'index.html';
        return;
    }

    const loginForm = document.getElementById('form-login');
    const registerForm = document.getElementById('form-register');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('login-email').value.trim();
            const password = document.getElementById('login-password').value.trim();
            const submitBtn = loginForm.querySelector('button[type="submit"]');

            await handleAuth(
                `${API_BASE}/auth/login`,
                { email, password },
                'Login successful!',
                submitBtn,
                'Sign In'
            );
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('reg-email').value.trim();
            const password = document.getElementById('reg-password').value.trim();
            const submitBtn = registerForm.querySelector('button[type="submit"]');

            await handleAuth(
                `${API_BASE}/auth/register`,
                { email, password },
                'Registration successful! Logging in...',
                submitBtn,
                'Sign Up'
            );
        });
    }

    // Warm up the backend in background on page load
    pingBackend();
});

async function pingBackend() {
    try {
        await fetch("https://my-logic.onrender.com/api/health", { method: 'GET' });
    } catch (_) {}
}

async function handleAuth(url, credentials, successMessage, submitBtn, defaultBtnText) {
    let wakeTimer = null;
    try {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <span style="display:inline-flex; align-items:center; gap:0.5rem;">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation: spin 1s linear infinite;">
                        <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                    </svg>
                    Authenticating...
                </span>
            `;
        }

        // If taking more than 3 seconds, inform the user that server is waking up
        wakeTimer = setTimeout(() => {
            showToast("Server is waking up (Render cold start). Please wait...", "info");
        }, 3000);

        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        });

        clearTimeout(wakeTimer);

        const rawText = await res.text();
        let data;
        try {
            data = JSON.parse(rawText);
        } catch (parseError) {
            console.error("Response is NOT JSON:", rawText);
            throw new Error("Server returned an unexpected response. Please try again.");
        }

        if (!res.ok) {
            throw new Error(data.error || "Authentication failed");
        }

        if (!data.token) {
            throw new Error("Token not received from server");
        }

        // Save token & user email
        localStorage.setItem('token', data.token);
        localStorage.setItem('userEmail', credentials.email);
        showToast(successMessage, 'success');

        setTimeout(() => {
            window.location.href = 'index.html';
        }, 800);

    } catch (error) {
        if (wakeTimer) clearTimeout(wakeTimer);
        console.error("Auth Error:", error);
        showToast(error.message || "Something went wrong", 'error');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = defaultBtnText;
        }
    }
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✅' : (type === 'info' ? '⏳' : '❌');

    toast.innerHTML = `
        <span>${icon}</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
