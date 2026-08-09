/**
 * Hugging Face Gradio backend via public HTTP API (string-only endpoints).
 */

const SPACE = (import.meta.env.VITE_HF_SPACE || "http://127.0.0.1:7860").replace(
  /\/$/,
  "",
);

const TOKEN_KEY = "myremover_hf_token";
const USER_KEY = "myremover_hf_user";

function getStoredToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

function setStoredSession(token, user) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
    if (user) sessionStorage.setItem(USER_KEY, JSON.stringify(user));
    else sessionStorage.removeItem(USER_KEY);
  } catch {
    /* ignore */
  }
}

function getStoredUser() {
  try {
    const raw = sessionStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function friendlyError(msg) {
  const m = String(msg || "");
  if (/sleep|cold|starting|503|502|timeout|Failed to fetch|NetworkError|in error/i.test(m)) {
    return "Hugging Face Space is starting, sleeping, or in error. Open the Space page, wait until Running, then retry.";
  }
  return m.replace(/^Error:\s*/i, "") || "Request failed";
}

async function gradioCall(apiName, data, { timeoutMs = 180_000 } = {}) {
  const postUrl = `${SPACE}/gradio_api/call/${apiName}`;
  let postRes;
  try {
    postRes = await fetch(postUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data }),
    });
  } catch (err) {
    throw new Error(friendlyError(err.message));
  }

  if (!postRes.ok) {
    const t = await postRes.text().catch(() => "");
    throw new Error(friendlyError(t || `HTTP ${postRes.status}`));
  }

  const posted = await postRes.json();
  const eventId = posted.event_id;
  if (!eventId) {
    if (Array.isArray(posted.data)) return posted.data;
    throw new Error("Gradio did not return event_id.");
  }

  const streamUrl = `${SPACE}/gradio_api/call/${apiName}/${eventId}`;
  const started = Date.now();

  while (Date.now() - started < timeoutMs) {
    let res;
    try {
      res = await fetch(streamUrl);
    } catch (err) {
      throw new Error(friendlyError(err.message));
    }
    if (!res.ok) {
      const t = await res.text().catch(() => "");
      throw new Error(friendlyError(t || `HTTP ${res.status}`));
    }

    const text = await res.text();
    const lines = text.split("\n");
    let event = "data";
    for (const line of lines) {
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
        continue;
      }
      if (line.startsWith("data:")) {
        const payload = line.slice(5).trim();
        if (!payload) continue;
        let parsed;
        try {
          parsed = JSON.parse(payload);
        } catch {
          continue;
        }
        if (event === "error") {
          const msg =
            typeof parsed === "string"
              ? parsed
              : parsed?.error || parsed?.message || JSON.stringify(parsed);
          throw new Error(friendlyError(msg));
        }
        if (event === "complete" || Array.isArray(parsed)) {
          return Array.isArray(parsed) ? parsed : parsed?.data || [parsed];
        }
      }
    }

    try {
      const j = JSON.parse(text);
      if (Array.isArray(j)) return j;
      if (Array.isArray(j.data)) return j.data;
    } catch {
      /* poll */
    }

    await new Promise((r) => setTimeout(r, 400));
  }

  throw new Error("Timed out waiting for Hugging Face Space.");
}

function parseJsonPayload(raw) {
  if (raw == null) return null;
  if (typeof raw === "object") return raw;
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }
  return null;
}

async function fileToRawBase64(file) {
  const buf = await file.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

export const gradioApi = {
  mode: "gradio",

  async login(username, password) {
    const data = await gradioCall("login", [username, password]);
    const payload = parseJsonPayload(data[0]);
    if (!payload?.token) throw new Error(payload?.error || "Login failed.");
    setStoredSession(payload.token, payload.user);
    return payload.user;
  },

  async logout() {
    const token = getStoredToken();
    try {
      if (token) await gradioCall("logout", [token]);
    } catch {
      /* ignore */
    }
    setStoredSession(null, null);
    return { logged_out: true };
  },

  async session() {
    const token = getStoredToken();
    if (!token) return { authenticated: false, user: null };
    try {
      const data = await gradioCall("session", [token]);
      const payload = parseJsonPayload(data[0]);
      if (!payload?.authenticated) {
        setStoredSession(null, null);
        return { authenticated: false, user: null };
      }
      if (payload.user) setStoredSession(token, payload.user);
      return payload;
    } catch {
      const user = getStoredUser();
      if (user) return { authenticated: true, user };
      return { authenticated: false, user: null };
    }
  },

  async removeBackground(file) {
    const token = getStoredToken();
    if (!token) throw new Error("Please log in first.");
    const b64in = await fileToRawBase64(file);
    const data = await gradioCall("remove_bg", [b64in, token], {
      timeoutMs: 300_000,
    });
    let b64 = data[0];
    if (typeof b64 !== "string" || !b64) {
      throw new Error("No image returned from Space.");
    }
    if (b64.startsWith("data:")) b64 = b64.split(",")[1] || "";
    b64 = b64.replace(/\s/g, "");
    return {
      dataUrl: `data:image/png;base64,${b64}`,
      image_base64: b64,
      size_bytes: Math.floor((b64.length * 3) / 4),
      filename: "image-no-bg.png",
      mime_type: "image/png",
    };
  },

  listUsers: async () => {
    throw new Error("User management is not available on HF free Gradio mode.");
  },
  createUser: async () => {
    throw new Error("User management is not available on HF free Gradio mode.");
  },
  updateUser: async () => {
    throw new Error("User management is not available on HF free Gradio mode.");
  },
  deleteUser: async () => {
    throw new Error("User management is not available on HF free Gradio mode.");
  },
  resetPassword: async () => {
    throw new Error("User management is not available on HF free Gradio mode.");
  },
  health: async () => ({ status: "ok", backend: "gradio", space: SPACE }),
};

export default gradioApi;
