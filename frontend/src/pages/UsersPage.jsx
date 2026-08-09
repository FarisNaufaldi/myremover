import React, { useCallback, useEffect, useState } from "react";
import api from "../api/client.js";
import { useAuth } from "../lib/AuthContext.jsx";
import UserForm from "../components/users/UserForm.jsx";
import DeleteUserDialog from "../components/users/DeleteUserDialog.jsx";
import Modal from "../components/shared/Modal.jsx";
import Toast from "../components/shared/Toast.jsx";

export default function UsersPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [resetUser, setResetUser] = useState(null);
  const [deleteUser, setDeleteUser] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (q = search) => {
    try {
      setError(null);
      const data = await api.listUsers(q);
      setUsers(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    load("");
  }, []); // initial

  useEffect(() => {
    const t = setTimeout(() => {
      setLoading(true);
      load(search);
    }, 220);
    return () => clearTimeout(t);
  }, [search]); // eslint-disable-line react-hooks/exhaustive-deps

  const showToast = (message, tone = "success") => setToast({ message, tone });

  const onCreate = async (payload) => {
    setBusy(true);
    try {
      await api.createUser(payload);
      setCreateOpen(false);
      showToast("User created.");
      await load();
    } catch (err) {
      throw err;
    } finally {
      setBusy(false);
    }
  };

  const onUpdate = async (payload) => {
    if (!editUser) return;
    setBusy(true);
    try {
      await api.updateUser(editUser.id, payload);
      setEditUser(null);
      showToast("User updated.");
      await load();
    } catch (err) {
      throw err;
    } finally {
      setBusy(false);
    }
  };

  const onReset = async (password) => {
    if (!resetUser) return;
    setBusy(true);
    try {
      await api.resetPassword(resetUser.id, password);
      setResetUser(null);
      showToast("Password reset.");
    } catch (err) {
      throw err;
    } finally {
      setBusy(false);
    }
  };

  const onDelete = async () => {
    if (!deleteUser) return;
    setBusy(true);
    try {
      await api.deleteUser(deleteUser.id);
      setDeleteUser(null);
      showToast("User deleted.");
      await load();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setBusy(false);
    }
  };

  const toggleActive = async (u) => {
    try {
      await api.updateUser(u.id, { is_active: !u.is_active });
      showToast(u.is_active ? "User disabled." : "User enabled.");
      await load();
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <span className="pill">Admin</span>
          <h1 className="display-heading mt-3 text-[44px] leading-[1.05] md:text-[56px]">
            Users
          </h1>
          <p className="mt-2 max-w-xl text-sm text-slate-400">
            Invite people by creating accounts — no public sign-up.
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={() => setCreateOpen(true)}>
          + Add User
        </button>
      </header>

      <div className="relative max-w-md">
        <input
          type="search"
          className="input w-full rounded-full py-3 pl-11 pr-4"
          placeholder="Search users…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search users"
        />
        <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="7" />
            <path d="m21 21-4.3-4.3" />
          </svg>
        </span>
      </div>

      {error && (
        <div className="card border-rose-500/40 text-sm text-rose-300">{error}</div>
      )}

      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead>
              <tr className="border-b border-white/[0.06] text-[10.5px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                <th className="px-5 py-3.5">Name</th>
                <th className="px-5 py-3.5">Username</th>
                <th className="px-5 py-3.5">Role</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={5} className="px-5 py-10 text-center text-slate-500">
                    Loading users…
                  </td>
                </tr>
              )}
              {!loading && users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-10 text-center text-slate-500">
                    No users found.
                  </td>
                </tr>
              )}
              {!loading &&
                users.map((u) => (
                  <tr
                    key={u.id}
                    className="border-b border-white/[0.04] transition hover:bg-white/[0.03]"
                  >
                    <td className="px-5 py-3.5 font-medium text-white">{u.name}</td>
                    <td className="px-5 py-3.5 text-slate-300">{u.username}</td>
                    <td className="px-5 py-3.5">
                      <span className="pill">{u.role}</span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center gap-1.5 text-xs font-medium ${
                          u.is_active ? "text-emerald-300" : "text-slate-500"
                        }`}
                      >
                        <span
                          className={`h-1.5 w-1.5 rounded-full ${
                            u.is_active ? "bg-emerald-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]" : "bg-slate-600"
                          }`}
                        />
                        {u.is_active ? "Active" : "Disabled"}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex flex-wrap items-center justify-end gap-1.5">
                        <button
                          type="button"
                          className="rounded-full px-2.5 py-1 text-xs text-slate-300 transition hover:bg-white/[0.06] hover:text-white"
                          onClick={() => setEditUser(u)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          className="rounded-full px-2.5 py-1 text-xs text-slate-300 transition hover:bg-white/[0.06] hover:text-white"
                          onClick={() => setResetUser(u)}
                        >
                          Reset password
                        </button>
                        <button
                          type="button"
                          className="rounded-full px-2.5 py-1 text-xs text-slate-300 transition hover:bg-white/[0.06] hover:text-white"
                          onClick={() => toggleActive(u)}
                          disabled={u.id === me?.id}
                        >
                          {u.is_active ? "Disable" : "Enable"}
                        </button>
                        <button
                          type="button"
                          className="rounded-full px-2.5 py-1 text-xs text-rose-300 transition hover:bg-rose-500/10"
                          onClick={() => setDeleteUser(u)}
                          disabled={u.id === me?.id}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Add User">
        <UserForm
          mode="create"
          busy={busy}
          onSubmit={onCreate}
          onCancel={() => setCreateOpen(false)}
        />
      </Modal>

      <Modal open={!!editUser} onClose={() => setEditUser(null)} title="Edit User">
        {editUser && (
          <UserForm
            mode="edit"
            initial={editUser}
            busy={busy}
            onSubmit={onUpdate}
            onCancel={() => setEditUser(null)}
          />
        )}
      </Modal>

      <Modal open={!!resetUser} onClose={() => setResetUser(null)} title="Reset Password">
        {resetUser && (
          <UserForm
            mode="reset"
            initial={resetUser}
            busy={busy}
            onSubmit={(p) => onReset(p.password)}
            onCancel={() => setResetUser(null)}
          />
        )}
      </Modal>

      <DeleteUserDialog
        open={!!deleteUser}
        user={deleteUser}
        busy={busy}
        onConfirm={onDelete}
        onCancel={() => setDeleteUser(null)}
      />

      <Toast
        message={toast?.message}
        tone={toast?.tone}
        onDismiss={() => setToast(null)}
      />
    </div>
  );
}
