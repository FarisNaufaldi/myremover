import React from "react";
import { MeshGradient } from "@paper-design/shaders-react";

const DARK_PALETTE = ["#000000", "#1e1b4b", "#4c1d95", "#7c3aed", "#a855f7", "#0a0118"];
const LIGHT_PALETTE = ["#ffffff", "#e6e6e6", "#bcbcbc", "#9e9e9e", "#d4d4d4", "#f4f4f4"];

export default function AmbientBackdrop({ theme = "dark" }) {
  const isLight = theme === "light";
  return (
    <div
      aria-hidden
      className={`pointer-events-none fixed inset-0 -z-10 overflow-hidden ${
        isLight ? "bg-[#f4f4f4]" : "bg-black"
      }`}
    >
      <MeshGradient
        colors={isLight ? LIGHT_PALETTE : DARK_PALETTE}
        distortion={0.85}
        swirl={0.55}
        grainMixer={isLight ? 0.32 : 0.38}
        grainOverlay={isLight ? 0.06 : 0.07}
        speed={0.35}
        scale={1.1}
        style={{ width: "100%", height: "100%" }}
      />
      <div className={`absolute inset-0 ${isLight ? "bg-[#f4f4f4]/25" : "bg-black/55"}`} />
      <div
        className={`absolute inset-0 ${
          isLight
            ? "bg-[radial-gradient(ellipse_at_center,transparent_30%,rgba(0,0,0,0.18)_100%)]"
            : "bg-[radial-gradient(ellipse_at_center,transparent_30%,rgba(0,0,0,0.65)_100%)]"
        }`}
      />
    </div>
  );
}
