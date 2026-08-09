import React from "react";

/**
 * MyRemover mark — subject cutout + transparency checker + spark.
 * Pass className / size. Unique gradient id via suffix to avoid collisions.
 */
export default function BrandLogo({ size = 20, id = "brand", className = "" }) {
  const gid = `mr-grad-${id}`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      <defs>
        <linearGradient id={gid} x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#e9d5ff" />
          <stop offset="50%" stopColor="#a78bfa" />
          <stop offset="100%" stopColor="#6d28d9" />
        </linearGradient>
      </defs>
      <rect x="3" y="3" width="26" height="26" rx="8" fill={`url(#${gid})`} opacity="0.22" />
      <rect
        x="3.75"
        y="3.75"
        width="24.5"
        height="24.5"
        rx="7.25"
        stroke={`url(#${gid})`}
        strokeWidth="1.5"
        opacity="0.9"
      />
      <g opacity="0.55">
        <rect x="7" y="20" width="3" height="3" fill="#c4b5fd" />
        <rect x="10" y="20" width="3" height="3" fill="#4c1d95" />
        <rect x="13" y="20" width="3" height="3" fill="#c4b5fd" />
        <rect x="7" y="23" width="3" height="3" fill="#4c1d95" />
        <rect x="10" y="23" width="3" height="3" fill="#c4b5fd" />
        <rect x="13" y="23" width="3" height="3" fill="#4c1d95" />
      </g>
      <path
        d="M11 18.5c0-4.2 2.6-7.5 5.8-7.5 1.7 0 3.2.9 4.2 2.3.8-1 2-1.6 3.4-1.6 2.6 0 4.6 2.6 4.6 6.2 0 4.4-2.8 7.6-6.3 7.6-1.4 0-2.6-.5-3.6-1.3-.9.7-2 1.1-3.2 1.1-2.9 0-4.9-2.8-4.9-6.8z"
        fill={`url(#${gid})`}
      />
      <path
        d="M22 6.2 L22.6 8.2 L24.6 8.8 L22.6 9.4 L22 11.4 L21.4 9.4 L19.4 8.8 L21.4 8.2 Z"
        fill="#e9d5ff"
      />
    </svg>
  );
}
