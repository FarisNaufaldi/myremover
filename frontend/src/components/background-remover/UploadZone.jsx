import React, { useCallback, useRef, useState } from "react";

const ACCEPT = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
const ACCEPT_EXT = [".jpg", ".jpeg", ".png", ".webp"];

function isAllowed(file) {
  if (!file) return false;
  const mime = (file.type || "").toLowerCase();
  if (mime && ACCEPT.includes(mime)) return true;
  const name = (file.name || "").toLowerCase();
  return ACCEPT_EXT.some((ext) => name.endsWith(ext));
}

export default function UploadZone({ onFile, onError }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = useCallback(
    (list) => {
      const file = list?.[0];
      if (!file) return;
      if (!isAllowed(file)) {
        onError?.("Unsupported image format. Please upload JPG, PNG, or WEBP.");
        return;
      }
      onError?.(null);
      onFile?.(file);
    },
    [onFile, onError],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      onClick={() => inputRef.current?.click()}
      onDragEnter={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(true);
      }}
      onDragOver={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(false);
      }}
      onDrop={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(false);
        handleFiles(e.dataTransfer.files);
      }}
            className={`card relative flex min-h-[280px] cursor-pointer flex-col items-center justify-center border-dashed text-center transition-all duration-300 ${
        dragOver
          ? "border-slate-400/50 bg-white/[0.06] scale-[1.01]"
          : "border-white/[0.12] hover:border-white/[0.2]"
      }`}
      style={{ borderStyle: "dashed" }}
      aria-label="Upload image"
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
        className="sr-only"
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
      />

      <div className="glass-panel mb-5 flex h-16 w-16 items-center justify-center rounded-full text-slate-300">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
          <path d="M12 16V4" strokeLinecap="round" />
          <path d="M7 9l5-5 5 5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" strokeLinecap="round" />
        </svg>
      </div>

      <h3 className="font-display text-2xl text-white">
        {dragOver ? "Drop image here" : "Upload Image"}
      </h3>
      <p className="mt-2 max-w-sm text-sm text-slate-400">
        {dragOver
          ? "Release to upload"
          : "Drag & drop your image here, or browse from your device."}
      </p>
      <span className="pill mt-5">JPG · PNG · WEBP</span>
    </div>
  );
}
