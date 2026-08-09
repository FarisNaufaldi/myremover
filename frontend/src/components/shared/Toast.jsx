import React, { useEffect } from "react";

/**
 * Lightweight toast stack — fixed bottom, auto-dismiss.
 */
export default function Toast({ message, tone = "info", onDismiss, ms = 4200 }) {
  useEffect(() => {
    if (!message) return undefined;
    const t = window.setTimeout(() => onDismiss?.(), ms);
    return () => window.clearTimeout(t);
  }, [message, ms, onDismiss]);

  if (!message) return null;

  const toneClass =
    tone === "error"
      ? "border-rose-500/40 text-rose-200"
      : tone === "success"
        ? "border-emerald-500/40 text-emerald-200"
        : "border-white/[0.12] text-slate-100";

  return (
    <div
      role="status"
      className={`fixed bottom-6 left-1/2 z-[90] max-w-md -translate-x-1/2 px-4 animate-[fadeIn_180ms_ease-out]`}
    >
      <div className={`glass-panel rounded-full px-5 py-3 text-sm shadow-pill ${toneClass}`}>
        {message}
      </div>
    </div>
  );
}
