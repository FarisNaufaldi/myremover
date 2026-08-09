import React, { useCallback, useRef, useState } from "react";

/**
 * Interactive before/after slider with polished checkerboard under transparent areas.
 */
export default function BeforeAfterViewer({ beforeUrl, afterUrl, width, height }) {
  const [pos, setPos] = useState(50);
  const dragging = useRef(false);
  const trackRef = useRef(null);

  const updateFromClientX = useCallback((clientX) => {
    const el = trackRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = Math.min(Math.max(clientX - rect.left, 0), rect.width);
    setPos((x / rect.width) * 100);
  }, []);

  const onPointerDown = (e) => {
    dragging.current = true;
    e.currentTarget.setPointerCapture?.(e.pointerId);
    updateFromClientX(e.clientX);
  };
  const onPointerMove = (e) => {
    if (!dragging.current) return;
    updateFromClientX(e.clientX);
  };
  const onPointerUp = () => {
    dragging.current = false;
  };

  const aspect = width && height ? width / height : 4 / 3;

  return (
    <div className="card p-3 md:p-4">
      <div className="mb-3 flex items-center justify-between px-1 text-[10.5px] font-semibold uppercase tracking-[0.14em] text-slate-500">
        <span>Before</span>
        <span>After</span>
      </div>
      <div
        ref={trackRef}
        className="relative w-full select-none overflow-hidden rounded-2xl"
        style={{
          aspectRatio: `${aspect}`,
          maxHeight: "min(70vh, 640px)",
          backgroundImage:
            "linear-gradient(45deg, #2a2a30 25%, transparent 25%), linear-gradient(-45deg, #2a2a30 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #2a2a30 75%), linear-gradient(-45deg, transparent 75%, #2a2a30 75%)",
          backgroundSize: "20px 20px",
          backgroundPosition: "0 0, 0 10px, 10px -10px, -10px 0px",
          backgroundColor: "#1a1a1e",
        }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
        role="slider"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(pos)}
        aria-label="Before and after comparison"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") setPos((p) => Math.max(0, p - 3));
          if (e.key === "ArrowRight") setPos((p) => Math.min(100, p + 3));
        }}
      >
        {/* After (full) */}
        <img
          src={afterUrl}
          alt="Background removed"
          className="absolute inset-0 h-full w-full object-contain"
          draggable={false}
        />
        {/* Before (clipped) */}
        <div
          className="absolute inset-0 overflow-hidden"
          style={{ width: `${pos}%` }}
        >
          <img
            src={beforeUrl}
            alt="Original"
            className="absolute inset-0 h-full max-w-none object-contain"
            style={{ width: trackRef.current?.clientWidth || "100%" }}
            draggable={false}
          />
        </div>
        {/* Divider */}
        <div
          className="absolute inset-y-0 z-10 w-0.5 bg-white shadow-[0_0_12px_rgba(255,255,255,0.45)]"
          style={{ left: `${pos}%` }}
        >
          <div className="absolute left-1/2 top-1/2 flex h-10 w-10 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-white/30 bg-black/60 shadow-pill backdrop-blur-md">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M8 12H4M20 12h-4M8 12l-3-3M8 12l-3 3M16 12l3-3M16 12l3 3" strokeLinecap="round" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
}
