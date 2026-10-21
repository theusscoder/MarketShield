
const API_BASE_URL = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : `Request failed (${response.status})`
    );
  }

  return data;
}

export async function signup({ name, email, password }) {
  const data = await request("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });

  return { user: data.user };
}

export async function login({ email, password }) {
  const data = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  return { user: data.user };
}

export async function getCurrentUser() {
  try {
    return await request("/auth/me");
  } catch (error) {
    if (
      error.message === "Please sign in." ||
      error.message.includes("session has expired") ||
      error.message.includes("(401)")
    ) {
      return null;
    }

    throw error;
  }
}

export async function logout() {
  return request("/auth/logout", { method: "POST" });
}
