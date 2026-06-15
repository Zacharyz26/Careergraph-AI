"use client";

import { useId, useState } from "react";

import type { ResumeUploadResponse } from "@/lib/types";

type ResumeUploaderProps = {
  upload?: ResumeUploadResponse | null;
  isLoading?: boolean;
  error?: string | null;
  onUpload: (file: File) => void | Promise<void>;
};

export function ResumeUploader({
  upload = null,
  isLoading = false,
  error = null,
  onUpload,
}: ResumeUploaderProps) {
  const inputId = useId();
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [pendingFilename, setPendingFilename] = useState<string | null>(null);

  function selectFile(file?: File) {
    if (!file) return;

    const extension = file.name.split(".").pop()?.toLowerCase();
    if (extension !== "pdf" && extension !== "docx") {
      setValidationError("Choose a PDF or DOCX resume.");
      return;
    }

    setValidationError(null);
    setPendingFilename(file.name);
    void onUpload(file);
  }

  return (
    <section className="card workflow-card">
      <div className="card-heading">
        <div>
          <span className="eyebrow">Step 1</span>
          <h2>Upload your resume</h2>
          <p>PDF or DOCX, up to the limits configured by the API.</p>
        </div>
        {upload ? <span className="status-badge status-badge--success">Extracted</span> : null}
      </div>

      <label
        className={`drop-zone${isDragging ? " drop-zone--active" : ""}`}
        onDragEnter={(event) => {
          event.preventDefault();
          if (isLoading) return;
          setIsDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setIsDragging(false);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          if (isLoading) return;
          selectFile(event.dataTransfer.files[0]);
        }}
        aria-disabled={isLoading}
        htmlFor={inputId}
      >
        <span className="upload-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24">
            <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 15v3.5A1.5 1.5 0 006.5 20h11a1.5 1.5 0 001.5-1.5V15" />
          </svg>
        </span>
        <strong>
          {isLoading
            ? `Uploading ${pendingFilename ?? "resume"}…`
            : "Drop your resume here"}
        </strong>
        <span>{isLoading ? "Extracting text from your document" : "or click to browse your files"}</span>
        <span className="file-types">PDF · DOCX</span>
        <input
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          disabled={isLoading}
          id={inputId}
          onChange={(event) => {
            selectFile(event.target.files?.[0]);
            event.target.value = "";
          }}
          type="file"
        />
      </label>

      {validationError || error ? (
        <p className="upload-error" role="alert">
          {validationError ?? error}
        </p>
      ) : null}

      {upload ? (
        <div className="file-summary">
          <span className="file-type-icon">{upload.file_type.toUpperCase()}</span>
          <div>
            <strong>{upload.filename}</strong>
            <p>
              {upload.character_count.toLocaleString()} characters
              {upload.page_count ? ` · ${upload.page_count} pages` : ""}
            </p>
          </div>
          <span className="check-mark" aria-label="Upload complete">
            ✓
          </span>
        </div>
      ) : null}
    </section>
  );
}
