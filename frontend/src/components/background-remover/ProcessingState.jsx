import React from "react";

export default function ProcessingState({ stage, filename }) {
  return (
    <div className="card flex flex-col items-center py-14 text-center">
      <div className="relative mb-6 flex h-16 w-16 items-center justify-center">
        <div className="processing-spinner-ring absolute inset-0 rounded-full border anim-spin-slow" />
        <div className="processing-spinner-ring absolute inset-2 rounded-full border opacity-50" />
        <div className="processing-spinner-dot h-3 w-3 rounded-full" />
      </div>
      <span className="pill">Processing</span>
      <h3 className="display-heading mt-4 text-3xl text-white">{stage}</h3>
      {filename && (
        <p className="mt-2 max-w-md truncate text-sm text-slate-500">{filename}</p>
      )}
      <p className="mt-4 text-xs text-slate-600">
        This may take a moment on large images or CPU inference.
      </p>
    </div>
  );
}
