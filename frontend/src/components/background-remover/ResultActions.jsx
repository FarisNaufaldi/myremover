import React from "react";

export default function ResultActions({ onDownload, onAnother, meta }) {
  return (
    <div className="flex flex-col items-stretch justify-between gap-4 sm:flex-row sm:items-center">
      <p className="text-sm text-slate-500">{meta}</p>
      <div className="flex flex-wrap gap-3">
        <button type="button" className="btn-primary" onClick={onDownload}>
          Download PNG
        </button>
        <button type="button" className="btn-ghost" onClick={onAnother}>
          Remove Another Image
        </button>
      </div>
    </div>
  );
}
