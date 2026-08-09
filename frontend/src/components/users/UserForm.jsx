import React, { useState } from "react";

export default function UserForm({ mode, initial, onSubmit, onCancel, busy }) {
  const isCreate = mode === "create";
  const isEdit = mode === "edit";
  const isReset = mode === "reset";

  const [name, setName] = useState(initial?.name || "");
  const [username, setUsername] = useState(initial?.username || "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(initial?.role || "USER");
  const [isActive, setIsActive] = useState(
    initial?.is_active === undefined ? true : initial.is_active,
  );
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      if (isReset) {
        if (password.length < 8) {
          setError("Password must be at least 8 characters.");
          return;
        }
        await onSubmit({ password });
        return;
      }
      if (isCreate) {
        if (!name.trim() || !username.trim() || password.length < 8) {
          setError("Name, username, and a password of at least 8 characters are required.");
          return;
        }
        await onSubmit({
          name: name.trim(),
          username: username.trim(),
          password,
          role,
        });
        return;
      }
      if (isEdit) {
        await onSubmit({
          name: name.trim(),
          username: username.trim(),
          role,
          is_active: isActive,
        });
      }
    } catch (err) {
      setError(err.message || "Something went wrong.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {!isReset && (
        <>
          <div>
            <label className="label" htmlFor="uf-name">
              Name
            </label>
            <input
              id="uf-name"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label" htmlFor="uf-username">
              Username
            </label>
            <input
              id="uf-username"
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="off"
            />
          </div>
        </>
      )}

      {(isCreate || isReset) && (
        <div>
          <label className="label" htmlFor="uf-password">
            Password
          </label>
          <input
            id="uf-password"
            type="password"
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
          />
          <p className="mt-1.5 text-xs text-slate-500">Minimum 8 characters.</p>
        </div>
      )}

      {isCreate && (
        <div>
          <label className="label" htmlFor="uf-role">
            Role
          </label>
          <select
            id="uf-role"
            className="input"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="USER">USER</option>
            <option value="ADMIN">ADMIN</option>
          </select>
        </div>
      )}

      {isEdit && (
        <>
          <div>
            <label className="label" htmlFor="uf-role-edit">
              Role
            </label>
            <select
              id="uf-role-edit"
              className="input"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              <option value="USER">USER</option>
              <option value="ADMIN">ADMIN</option>
            </select>
          </div>
          <div>
            <label className="label" htmlFor="uf-status">
              Status
            </label>
            <select
              id="uf-status"
              className="input"
              value={isActive ? "active" : "disabled"}
              onChange={(e) => setIsActive(e.target.value === "active")}
            >
              <option value="active">Active</option>
              <option value="disabled">Disabled</option>
            </select>
          </div>
        </>
      )}

      {error && (
        <div role="alert" className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-200">
          {error}
        </div>
      )}

      <div className="flex flex-wrap justify-end gap-2 pt-2">
        <button type="button" className="btn-ghost" onClick={onCancel} disabled={busy}>
          Cancel
        </button>
        <button type="submit" className="btn-primary" disabled={busy}>
          {busy
            ? "Saving…"
            : isCreate
              ? "Create"
              : isReset
                ? "Reset password"
                : "Save"}
        </button>
      </div>
    </form>
  );
}
