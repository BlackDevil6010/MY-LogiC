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

            await handleAuth(
                `${API_BASE}/auth/login`,
                { email, password },
                'Login successful!'
            );
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('reg-email').value.trim();
            const password = document.getElementById('reg-password').value.trim();

            await handleAuth(
                `${API_BASE}/auth/register`,
                { email, password },
                'Registration successful! Logging in...'
            );
        });
    }
});

async function handleAuth(url, credentials, successMessage) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        });

        // 🔥 Always read raw text first
        const rawText = await res.text();
        console.log("Server Raw Response:", rawText);

        let data;
        try {
            data = JSON.parse(rawText);
        } catch (parseError) {
            console.error("Response is NOT JSON:", rawText);
            throw new Error("Server returned invalid response. Check backend logs.");
        }

        if (!res.ok) {
            throw new Error(data.error || "Authentication failed");
        }

        if (!data.token) {
            throw new Error("Token not received from server");
        }

        // Save token
        localStorage.setItem('token', data.token);
        localStorage.setItem('userEmail', credentials.email);
        showToast(successMessage, 'success');

        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);

    } catch (error) {
        console.error("Auth Error:", error);
        showToast(error.message || "Something went wrong", 'error');
    }
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '✅' : '❌';
    
    toast.innerHTML = `
        <span>${icon}</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}


