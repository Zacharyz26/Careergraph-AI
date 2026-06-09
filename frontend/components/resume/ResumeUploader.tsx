export function ResumeUploader() {
  return (
    <section className="panel">
      <h2>Resume document</h2>
      <p className="muted">
        Placeholder for validated upload, processing status, and parsing errors.
      </p>
      <input aria-label="Resume file" type="file" accept=".pdf,.docx" disabled />
    </section>
  );
}
