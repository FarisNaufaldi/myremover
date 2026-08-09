/**
 * Hugging Face Gradio backend via public HTTP API (no Node deps).
 * Space free tier may sleep; first call after idle can take 30–90s.
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
  if (/sleep|cold|starting|503|502|timeout|Failed to fetch|NetworkError/i.test(m)) {
    return "Hugging Face Space is starting or sleeping (free tier). Wait 30–90s and try again.";
  }
  return m.replace(/^Error:\s*/i, "") || "Request failed";
}

/**
 * Gradio 4 queue API:
 * POST /gradio_api/call/{api_name}  { data: [...] }
 * then poll GET /gradio_api/call/{api_name}/{event_id}
 */
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
    // Some versions return data directly
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
    // SSE-style: event: complete\ndata: [...]
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

    // Non-SSE JSON fallback
    try {
      const j = JSON.parse(text);
      if (Array.isArray(j)) return j;
      if (Array.isArray(j.data)) return j.data;
    } catch {
      /* keep polling */
    }

    await new Promise((r) => setTimeout(r, 400));
  }

  throw new Error("Timed out waiting for Hugging Face Space.");
}

async function fileToGradioImagePayload(file) {
  // Gradio accepts file as base64 data URL or binary upload path.
  // Browser: send as object with path via base64.
  const buf = await file.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  const b64 = btoa(binary);
  const mime = file.type || "image/png";
  return {
    path: null,
    url: `data:${mime};base64,${b64}`,
    orig_name: file.name || "upload.png",
    meta: { _type: "gradio.FileData" },
  };
}

async function imageResultToPayload(out) {
  if (!out) throw new Error("No image returned from Space.");
  let url = null;
  if (typeof out === "string") url = out;
  else if (out.url) url = out.url;
  else if (out.path && String(out.path).startsWith("http")) url = out.path;
  else if (out.path && String(out.path).startsWith("data:")) url = out.path;
  else if (out.data && typeof out.data === "string") {
    if (out.data.startsWith("data:")) {
      return {
        dataUrl: out.data,
        image_base64: out.data.split(",")[1] || "",
        size_bytes: 0,
        filename: "image-no-bg.png",
        mime_type: "image/png",
      };
    }
  }

  if (!url) throw new Error("Unexpected image payload from Space.");
  if (url.startsWith("/")) url = `${SPACE}${url}`;
  if (url.startsWith("data:")) {
    return {
      dataUrl: url,
      image_base64: url.split(",")[1] || "",
      size_bytes: 0,
      filename: "image-no-bg.png",
      mime_type: "image/png",
    };
  }

  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to download result image.");
  const blob = await res.blob();
  const buf = await blob.arrayBuffer();
  const bytes = new Uint8Array(buf);
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  const b64 = btoa(binary);
  return {
    dataUrl: `data:image/png;base64,${b64}`,
    image_base64: b64,
    size_bytes: bytes.length,
    filename: "image-no-bg.png",
    mime_type: "image/png",
  };
}

export const gradioApi = {
  mode: "gradio",

  async function login(username, password) {
    const data = await gradioCall("login", [username, password]);
    const raw = data[0];
    const payload = typeof raw === "string" ? JSON.parse(raw) : raw;
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
      const raw = data[0];
      const payload = typeof raw === "string" ? JSON.parse(raw) : raw;
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
    const imagePayload = await fileToGradioImagePayload(file);
    // Prefer raw File — Gradio API often accepts file as last try via path URL
    let data;
    try {
      data = await gradioCall("remove_bg", [imagePayload, token], {
        timeoutMs: 300_000,
      });
    } catch (err) {
      // Fallback: pass File object via Form... if fails rethrow first
      throw err;
    }
    return imageResultToPayload(data[0]);
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
