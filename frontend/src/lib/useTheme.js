import { useEffect, useState } from "react";

function readAttribute() {
  if (typeof document === "undefined") return "dark";
  return document.documentElement.getAttribute("data-theme") || "dark";
}

export function useThemeAttribute() {
  const [theme, setTheme] = useState(readAttribute);

  useEffect(() => {
    const obs = new MutationObserver(() => {
      setTheme(readAttribute());
    });
    obs.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => obs.disconnect();
  }, []);

  return theme;
}
