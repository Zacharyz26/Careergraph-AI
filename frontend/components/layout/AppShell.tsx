import Link from "next/link";
import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <Link className="brand" href="/">
            <span className="brand-mark" aria-hidden="true">
              <svg viewBox="0 0 40 40">
                <path className="brand-mark__sheet" d="M11 6.5h13.6L31 12.9v20.6H11z" />
                <path className="brand-mark__fold" d="M24.6 6.5v6.4H31" />
                <path className="brand-mark__line" d="M15.5 15.2h6.2M15.5 19.2h4.4" />
                <path className="brand-mark__path" d="M15.7 28.2l4.2-4.6 3.4 2.8 5.1-7" />
                <circle className="brand-mark__node" cx="15.7" cy="28.2" r="1.8" />
                <circle className="brand-mark__node" cx="19.9" cy="23.6" r="1.8" />
                <circle className="brand-mark__node" cx="23.3" cy="26.4" r="1.8" />
                <circle className="brand-mark__node" cx="28.4" cy="19.4" r="1.8" />
              </svg>
            </span>
            <span className="brand-wordmark">
              <span className="brand-name">CareerGraph</span>
              <span className="brand-ai">AI</span>
            </span>
          </Link>
          <div className="header-meta">
            <span className="live-dot" aria-hidden="true" />
            Evidence-grounded advisor
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
