import { ResumeUploader } from "@/components/resume/ResumeUploader";

export default function UploadPage() {
  return (
    <main>
      <h1>Upload resume</h1>
      <p className="muted">PDF and DOCX ingestion will be connected here.</p>
      <ResumeUploader />
    </main>
  );
}
