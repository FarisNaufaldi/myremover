// API client.
// - Default: FastAPI same-origin /api (local, Render, Replit)
// - HF free + Vercel: VITE_BACKEND=gradio + VITE_HF_SPACE=https://….hf.space

import gradioApi from "./gradio.js";

const BACKEND = (import.meta.env.VITE_BACKEND || "fastapi").toLowerCase();
const API_BASE = (import.meta.env.VITE_API_BASE || "/api").replace(/\/$/, "");

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

  if (body && typeof body === "object" && "success" in body) {
    if (body.success === false) {
      throw new Error(body.error || "Request failed");
    }
    return body.data !== undefined ? body.data : body;
  }
  return body;
}

const fastapiApi = {
  mode: "fastapi",
  login: (username, password) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: () => request("/auth/logout", { method: "POST" }),
  session: () => request("/auth/session"),
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
  removeBackground: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request("/remove-background", { method: "POST", body: fd });
  },
  health: () => request("/health"),
};

const api = BACKEND === "gradio" ? gradioApi : fastapiApi;

export { BACKEND };
export default api;
