import Link from "next/link";

const workflows = [
  { href: "/upload", label: "Upload a resume" },
  { href: "/profile", label: "Review candidate profile" },
  { href: "/job-match", label: "Match a job description" },
  { href: "/suggestions", label: "Review suggestions" },
  { href: "/roadmap", label: "View career roadmap" },
];

export default function HomePage() {
  return (
    <main>
      <p className="muted">Evidence-grounded resume intelligence</p>
      <h1>CareerGraph AI</h1>
      <p>
        Turn resume evidence into a structured profile, explainable job matches,
        and user-reviewed improvement suggestions.
      </p>
      <section className="panel">
        <h2>MVP workflows</h2>
        <ul>
          {workflows.map((workflow) => (
            <li key={workflow.href}>
              <Link href={workflow.href}>{workflow.label}</Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
