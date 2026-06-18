import Link from "next/link";
import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <Link className="brand" href="/">
            <span className="brand-mark" aria-hidden="true">
              <svg viewBox="0 0 32 32">
                <circle cx="9" cy="9" r="3" />
                <circle cx="23" cy="8" r="3" />
                <circle cx="16" cy="23" r="3" />
                <path d="M11.5 10.5l9-1M10.5 11.5l4.5 9M21.5 10.5l-4.5 10" />
              </svg>
            </span>
            <span>
              CareerGraph <strong>AI</strong>
            </span>
          </Link>
          <div className="header-meta">
            <span className="live-dot" aria-hidden="true" />
            CareerGraph AI
          </div>
        </div>
      </header>
      {children}
      <footer className="site-footer">
        <p>CareerGraph AI</p>
      </footer>
    </>
  );
}
