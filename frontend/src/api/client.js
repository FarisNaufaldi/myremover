// API client. Dev proxy: /api → localhost:8000 (vite.config.js)

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

function extractError(body, status) {
  if (!body) return `HTTP ${status}`;
  if (typeof body.error === "string" && body.error) return body.error;
  if (typeof body.detail === "string" && body.detail) return body.detail;
  return `HTTP ${status}`;
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const isForm = options.body instanceof FormData;
  if (!isForm && options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...options,
    headers,
  });

  let body = null;
  const text = await res.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = null;
    }
  }

  if (!res.ok) {
    throw new Error(extractError(body, res.status));
  }

  // Prefer envelope data when present
  if (body && typeof body === "object" && "success" in body) {
    if (body.success === false) {
      throw new Error(body.error || "Request failed");
    }
    return body.data !== undefined ? body.data : body;
  }
  return body;
}

export const api = {
  // Auth
  login: (username, password) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: () => request("/auth/logout", { method: "POST" }),
  session: () => request("/auth/session"),

  // Users (admin)
  listUsers: (search = "") => {
    const q = search ? `?search=${encodeURIComponent(search)}` : "";
    return request(`/users${q}`);
  },
  createUser: (payload) =>
    request("/users", { method: "POST", body: JSON.stringify(payload) }),
  updateUser: (id, payload) =>
    request(`/users/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteUser: (id) => request(`/users/${id}`, { method: "DELETE" }),
  resetPassword: (id, password) =>
    request(`/users/${id}/reset-password`, {
      method: "POST",
      body: JSON.stringify({ password }),
    }),

  // Background removal
  removeBackground: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("/remove-background", { method: "POST", body: fd });
  },

  health: () => request("/health"),
};

export default api;
