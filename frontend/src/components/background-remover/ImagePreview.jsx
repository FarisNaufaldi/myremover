import React from "react";

export default function ImagePreview({
  file,
  previewUrl,
  sizeLabel,
  onRemove,
  onProcess,
  processing,
}) {
  return (
    <div className="card space-y-5">
      <div className="flex flex-col gap-5 md:flex-row md:items-start">
        <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-black/40 md:w-1/2">
          <img
            src={previewUrl}
            alt={file?.name || "Selected image preview"}
            className="max-h-[420px] w-full object-contain"
          />
        </div>
        <div className="flex flex-1 flex-col gap-4">
          <div>
            <div className="label">Selected file</div>
            <div className="truncate text-base text-white">{file?.name}</div>
            <div className="mt-1 text-sm text-slate-500">{sizeLabel}</div>
          </div>
          <div className="mt-auto flex flex-wrap gap-3">
            <button
              type="button"
              className="btn-primary"
              onClick={onProcess}
              disabled={processing}
            >
              Remove Background
            </button>
            <button type="button" className="btn-ghost" onClick={onRemove} disabled={processing}>
              Remove image
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
