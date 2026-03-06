// 🔥 Use fixed production backend URL (remove auto detection for now)
const API_BASE = "https://my-logic-production.up.railway.app/api";

document.addEventListener("DOMContentLoaded", () => {

  console.log("Auth JS Loaded");

  // Redirect if already logged in
  if (localStorage.getItem("token")) {
    window.location.href = "index.html";
  }

  const loginForm = document.getElementById("form-login");
  const registerForm = document.getElementById("form-register");

  // LOGIN
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const email = document.getElementById("login-email").value;
      const password = document.getElementById("login-password").value;

      await handleAuth(
        `${API_BASE}/auth/login`,
        { email, password },
        "Login successful!"
      );
    });
  }

  // REGISTER
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const email = document.getElementById("reg-email").value;
      const password = document.getElementById("reg-password").value;

      await handleAuth(
        `${API_BASE}/auth/register`,
        { email, password },
        "Registration successful! Logging in..."
      );
    });
  }
});

// 🔥 SAFE AUTH FUNCTION
async function handleAuth(url, credentials, successMessage) {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(credentials),
    });

    // 🔥 Check if response is JSON before parsing
    const contentType = res.headers.get("content-type");

    if (!contentType || !contentType.includes("application/json")) {
      const text = await res.text();
      console.error("Server returned non-JSON response:", text);
      throw new Error("Server error. Backend might be down.");
    }

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Authentication failed");
    }

    localStorage.setItem("token", data.token);
    localStorage.setItem("userEmail", data.email);

    showToast(successMessage, "success");

    setTimeout(() => {
      window.location.href = "index.html";
    }, 1000);

  } catch (err) {
    console.error("Auth Error:", err);
    showToast(err.message, "error");
  }
}

// TOAST
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  const icon = type === "success" ? "✅" : "❌";

  toast.innerHTML = `
        <span>${icon}</span>
        <span>${message}</span>
    `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "fadeOut 0.3s ease-in forwards";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
