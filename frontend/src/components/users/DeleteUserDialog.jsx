import React from "react";
import Modal from "../shared/Modal.jsx";

export default function DeleteUserDialog({ open, user, onConfirm, onCancel, busy }) {
  return (
    <Modal open={open} onClose={onCancel} title="Delete this user?">
      <p className="text-sm leading-relaxed text-slate-400">
        This action cannot be undone.
        {user && (
          <>
            {" "}
            You are about to permanently remove{" "}
            <span className="text-slate-200">{user.name}</span> (
            <span className="text-slate-200">{user.username}</span>).
          </>
        )}
      </p>
      <div className="mt-6 flex flex-wrap justify-end gap-2">
        <button type="button" className="btn-ghost" onClick={onCancel} disabled={busy}>
          Cancel
        </button>
        <button
          type="button"
          className="btn rounded-full bg-rose-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-rose-500 active:scale-[0.98]"
          onClick={onConfirm}
          disabled={busy}
        >
          {busy ? "Deleting…" : "Delete"}
        </button>
      </div>
    </Modal>
  );
}
