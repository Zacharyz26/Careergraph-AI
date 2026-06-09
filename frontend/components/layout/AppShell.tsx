import Link from "next/link";
import type { ReactNode } from "react";

const navigation = [
  ["Upload", "/upload"],
  ["Profile", "/profile"],
  ["Job match", "/job-match"],
  ["Suggestions", "/suggestions"],
  ["Roadmap", "/roadmap"],
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <header className="panel">
        <nav aria-label="Primary navigation">
          <Link href="/"><strong>CareerGraph AI</strong></Link>
          {" | "}
          {navigation.map(([label, href], index) => (
            <span key={href}>
              {index > 0 ? " | " : ""}
              <Link href={href}>{label}</Link>
            </span>
          ))}
        </nav>
      </header>
      {children}
    </>
  );
}
