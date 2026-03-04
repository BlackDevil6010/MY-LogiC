const API_BASE = 'http://localhost:5000/api';

document.addEventListener('DOMContentLoaded', () => {
    // If already logged in, redirect to dashboard
    if (localStorage.getItem('token')) {
        window.location.href = 'index.html';
    }

    const loginForm = document.getElementById('form-login');
    const registerForm = document.getElementById('form-register');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;

            await handleAuth(`${API_BASE}/auth/login`, { email, password }, 'Login successful!');
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;

            await handleAuth(`${API_BASE}/auth/register`, { email, password }, 'Registration successful! Logging in...');
        });
    }
});

async function handleAuth(url, credentials, successMessage) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credentials)
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || 'Authentication failed');
        }

        // Save token and user email 
        localStorage.setItem('token', data.token);
        localStorage.setItem('userEmail', data.email);
        showToast(successMessage, 'success');

        // Redirect to main dashboard
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);

    } catch (err) {
        showToast(err.message, 'error');
    }
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? '✅' : '❌';
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-in forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
