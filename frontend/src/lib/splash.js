import { useEffect } from "react";
import api from "../api/client.js";

const MIN_DISPLAY_MS = 700;
const MAX_DISPLAY_MS = 6000;

export function useSplashLifecycle() {
  useEffect(() => {
    const splash = document.getElementById("splash-screen");
    if (!splash) return undefined;

    const startedAt = performance.now();
    let alreadyHidden = false;

    const hide = () => {
      if (alreadyHidden) return;
      alreadyHidden = true;
      const elapsed = performance.now() - startedAt;
      const wait = Math.max(MIN_DISPLAY_MS - elapsed, 0);
      window.setTimeout(() => {
        splash.classList.add("is-hidden");
        window.setTimeout(() => splash.remove(), 600);
      }, wait);
    };

    const safetyTimer = window.setTimeout(hide, MAX_DISPLAY_MS);

    const fontsReady =
      document.fonts && document.fonts.ready
        ? document.fonts.ready
        : Promise.resolve();
    const sessionReady = api.session().catch(() => null);

    Promise.allSettled([fontsReady, sessionReady]).then(() => {
      window.clearTimeout(safetyTimer);
      hide();
    });

    return () => {
      window.clearTimeout(safetyTimer);
    };
  }, []);
}
