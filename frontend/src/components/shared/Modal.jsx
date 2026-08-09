import React, { useEffect } from "react";

/**
 * Accessible dialog — Escape to close, focus trap-lite, overlay click dismiss.
 * Visual language mirrors reference project glass panels.
 */
export default function Modal({
  open,
  onClose,
  title,
  children,
  wide = false,
}) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center px-4 py-8"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        aria-label="Close dialog"
        onClick={onClose}
      />
      <div
        className={`glass-panel relative z-10 w-full ${
          wide ? "max-w-2xl" : "max-w-md"
        } rounded-2xl p-6 shadow-2xl animate-[fadeIn_180ms_ease-out]`}
      >
        <div className="mb-5 flex items-start justify-between gap-4">
          <h2 className="font-display text-2xl text-white">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-white/[0.12] px-2.5 py-1 text-sm text-slate-300 transition hover:bg-white/[0.06] hover:text-white"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
