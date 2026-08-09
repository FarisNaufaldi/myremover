import React, { useCallback, useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import AmbientBackdrop from "./components/shared/AmbientBackdrop.jsx";
import BrandLogo from "./components/shared/BrandLogo.jsx";
import { ProtectedRoute } from "./components/shared/ProtectedRoute.jsx";
import { useAuth } from "./lib/AuthContext.jsx";
import { useSplashLifecycle } from "./lib/splash.js";
import LoginPage from "./pages/LoginPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import UsersPage from "./pages/UsersPage.jsx";
import { BACKEND } from "./api/client.js";

const THEME_STORAGE_KEY = "myremover-theme";

function readInitialTheme() {
  if (typeof window === "undefined") return "dark";
  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  return stored === "light" ? "light" : "dark";
}

function applyFavicon(theme) {
  if (typeof document === "undefined") return;
  const link = document.getElementById("favicon");
  if (!link) return;
  link.setAttribute(
    "href",
    theme === "light" ? "/favicon-light.svg" : "/favicon.svg",
  );
}

function useTheme() {
  const [theme, setTheme] = useState(readInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    applyFavicon(theme);
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((cur) => (cur === "light" ? "dark" : "light"));
  }, []);

  return { theme, toggle };
}

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "instant" });
  }, [pathname]);
  return null;
}

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      end={to === "/dashboard"}
      className={({ isActive }) => `nav-link ${isActive ? "nav-link-active" : ""}`}
    >
      {children}
    </NavLink>
  );
}

function Brand({ theme, onToggleTheme }) {
  const isLight = theme === "light";
  return (
    <div className="flex items-center gap-3 pl-2 pr-2">
      <button
        type="button"
        onClick={onToggleTheme}
        aria-label={isLight ? "Enable dark mode" : "Enable light mode"}
        title={isLight ? "Enable dark mode" : "Enable light mode"}
        className="brand-theme-toggle flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-all duration-300 ease-out hover:scale-110 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-400/60"
      >
        <BrandLogo size={22} id="nav" className="shrink-0" />
      </button>
      <NavLink to="/dashboard" className="font-display text-[20px] leading-none text-white">
        <span className="italic">My</span>Remover
      </NavLink>
    </div>
  );
}

function AppShell({ theme, toggle }) {
  const { user, isAdmin, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const hideChrome = location.pathname === "/login";

  return (
    <div className="relative min-h-screen">
      <ScrollToTop />
      <AmbientBackdrop theme={theme} />

      {!hideChrome && isAuthenticated && (
        <header className="fixed inset-x-0 top-4 z-50 flex justify-center px-4">
          <div className="nav-pill max-w-full flex-wrap justify-center gap-y-1">
            <Brand theme={theme} onToggleTheme={toggle} />
            <nav className="flex items-center gap-0.5">
              <NavItem to="/dashboard">Background Remover</NavItem>
              {isAdmin && BACKEND === "fastapi" && (
                <NavItem to="/users">Users</NavItem>
              )}
            </nav>
            <div className="ml-2 flex items-center gap-1.5">
              <span className="hidden items-center gap-2 rounded-full border border-white/[0.1] px-3 py-1.5 text-[12px] text-slate-300 sm:inline-flex">
                <span className="max-w-[10ch] truncate text-slate-100">{user?.username}</span>
                <span className="text-slate-500">·</span>
                <span className="text-slate-400">{user?.role}</span>
              </span>
              <button
                type="button"
                className="nav-cta"
                onClick={async () => {
                  await logout();
                  navigate("/login", { replace: true });
                }}
              >
                Logout
              </button>
            </div>
          </div>
        </header>
      )}

      {hideChrome && (
        <header className="fixed inset-x-0 top-4 z-50 flex justify-center px-4">
          <div className="nav-pill">
            <Brand theme={theme} onToggleTheme={toggle} />
          </div>
        </header>
      )}

      <main className="mx-auto max-w-6xl px-4 pb-16 pt-28 md:px-8">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          {BACKEND === "fastapi" && (
            <Route
              path="/users"
              element={
                <ProtectedRoute adminOnly>
                  <UsersPage />
                </ProtectedRoute>
              }
            />
          )}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>

      <footer className="border-t border-white/[0.05] px-4 py-8 text-center text-xs text-slate-600 md:px-8">
        MyRemover · Private AI Background Remover ·{" "}
        <span className="text-slate-500">
          {BACKEND === "gradio"
            ? "HF Gradio + Vercel"
            : "FastAPI + React + Tailwind"}
        </span>
      </footer>
    </div>
  );
}

export default function App() {
  const { theme, toggle } = useTheme();
  useSplashLifecycle();
  return <AppShell theme={theme} toggle={toggle} />;
}
