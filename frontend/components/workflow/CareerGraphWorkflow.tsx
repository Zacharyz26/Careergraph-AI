"use client";

import { useMemo, useState } from "react";

import { CareerDirectionCards } from "@/components/career/CareerDirectionCards";
import { JobMatchPanel } from "@/components/match/JobMatchPanel";
import { CandidateProfilePanel } from "@/components/resume/CandidateProfilePanel";
import { ResumeUploader } from "@/components/resume/ResumeUploader";
import { SuggestionPanel } from "@/components/suggestions/SuggestionPanel";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingState } from "@/components/ui/LoadingState";
import { WorkflowStepper } from "@/components/workflow/WorkflowStepper";
import {
  generateSuggestions,
  parseCandidateProfile,
  parseJobDescription,
  recommendCareerDirections,
  scoreJobMatch,
  uploadResume,
} from "@/lib/api";
import type {
  CandidateProfile,
  CareerDirection,
  JobProfile,
  MatchResult,
  ResumeUploadResponse,
  SuggestionResponse,
} from "@/lib/types";

type MainAction =
  | "upload"
  | "profile"
  | "directions"
  | "suggestions"
  | null;

export function CareerGraphWorkflow() {
  const [upload, setUpload] = useState<ResumeUploadResponse | null>(null);
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [directions, setDirections] = useState<CareerDirection[]>([]);
  const [selectedDirection, setSelectedDirection] = useState<CareerDirection | null>(null);
  const [suggestions, setSuggestions] = useState<SuggestionResponse | null>(null);
  const [jobProfile, setJobProfile] = useState<JobProfile | null>(null);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [mainAction, setMainAction] = useState<MainAction>(null);
  const [jobLoading, setJobLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);

  const currentStep = useMemo(() => {
    if (matchResult) return 5;
    if (suggestions) return 4;
    if (directions.length) return 3;
    if (profile) return 2;
    return 1;
  }, [directions.length, matchResult, profile, suggestions]);

  async function handleUpload(file: File) {
    setMainAction("upload");
    setUploadError(null);
    setUpload(null);
    setProfile(null);
    setDirections([]);
    setSelectedDirection(null);
    setSuggestions(null);
    setJobProfile(null);
    setMatchResult(null);
    try {
      setUpload(await uploadResume(file));
    } catch (cause) {
      setUploadError(messageFrom(cause));
    } finally {
      setMainAction(null);
    }
  }

  async function handleParseProfile() {
    if (!upload) return;
    setMainAction("profile");
    setError(null);
    try {
      setProfile(await parseCandidateProfile(upload.extracted_text));
    } catch (cause) {
      setError(messageFrom(cause));
    } finally {
      setMainAction(null);
    }
  }

  async function handleDirections() {
    if (!profile) return;
    setMainAction("directions");
    setError(null);
    try {
      const result = await recommendCareerDirections(profile);
      setDirections(result.directions);
      setSelectedDirection(result.directions[0] ?? null);
    } catch (cause) {
      setError(messageFrom(cause));
    } finally {
      setMainAction(null);
    }
  }

  async function handleSuggestions() {
    if (!profile || !selectedDirection) return;
    setMainAction("suggestions");
    setError(null);
    try {
      setSuggestions(
        await generateSuggestions({
          candidate_profile: profile,
          career_direction_result: selectedDirection,
          target_direction: selectedDirection.direction,
          suggestion_mode: "career_direction",
        }),
      );
    } catch (cause) {
      setError(messageFrom(cause));
    } finally {
      setMainAction(null);
    }
  }

  async function handleJobMatch(description: string) {
    if (!profile) return;
    setJobLoading(true);
    setJobError(null);
    setJobProfile(null);
    setMatchResult(null);
    try {
      const parsedJob = await parseJobDescription(description);
      setJobProfile(parsedJob);
      setMatchResult(await scoreJobMatch(profile, parsedJob));
    } catch (cause) {
      setJobError(messageFrom(cause));
    } finally {
      setJobLoading(false);
    }
  }

  return (
    <main className="workflow-page">
      <section className="hero">
        <div>
          <span className="hero-kicker">
            <span aria-hidden="true">✦</span> Evidence-grounded career intelligence
          </span>
          <h1>Turn your resume into a clearer career direction.</h1>
          <p>
            Upload once to uncover your strongest paths, improve your positioning,
            and compare your evidence against a real job.
          </p>
        </div>
        <div className="trust-card">
          <span className="trust-icon" aria-hidden="true">✓</span>
          <div>
            <strong>Your facts stay in control</strong>
            <p>No invented skills, metrics, or experience.</p>
          </div>
        </div>
      </section>

      <WorkflowStepper currentStep={currentStep} />

      {error ? <ErrorMessage message={error} onDismiss={() => setError(null)} /> : null}

      <div className="workflow-grid">
        <div className="workflow-controls">
          <ResumeUploader
            error={uploadError}
            isLoading={mainAction === "upload"}
            onUpload={handleUpload}
            upload={upload}
          />

          {upload ? (
            <section className="card action-card">
              <div>
                <span className="eyebrow">Step 2</span>
                <h2>Build your candidate profile</h2>
                <p>Convert extracted resume text into structured, reviewable evidence.</p>
              </div>
              <button
                className="button button--primary button--wide"
                disabled={mainAction !== null}
                onClick={handleParseProfile}
                type="button"
              >
                {mainAction === "profile" ? "Parsing profile…" : profile ? "Rebuild profile" : "Parse candidate profile"}
              </button>
              <details className="disclosure">
                <summary>View extracted resume text</summary>
                <pre>{upload.extracted_text}</pre>
              </details>
            </section>
          ) : null}

          {profile ? (
            <section className="card action-card">
              <div>
                <span className="eyebrow">Step 3</span>
                <h2>Discover career directions</h2>
                <p>Rank realistic paths using your skills, work, projects, and education.</p>
              </div>
              <button
                className="button button--primary button--wide"
                disabled={mainAction !== null}
                onClick={handleDirections}
                type="button"
              >
                {mainAction === "directions" ? "Ranking directions…" : directions.length ? "Refresh directions" : "Recommend career directions"}
              </button>
            </section>
          ) : null}

          {selectedDirection ? (
            <section className="card action-card action-card--accent">
              <div>
                <span className="eyebrow">Step 4</span>
                <h2>Improve resume positioning</h2>
                <p>Generate safe suggestions for <strong>{selectedDirection.direction}</strong>.</p>
              </div>
              <button
                className="button button--dark button--wide"
                disabled={mainAction !== null}
                onClick={handleSuggestions}
                type="button"
              >
                {mainAction === "suggestions" ? "Generating suggestions…" : "Generate improvement suggestions"}
              </button>
            </section>
          ) : null}
        </div>

        <aside className="workflow-results">
          {mainAction && mainAction !== "upload" ? (
            <LoadingState label={loadingLabel(mainAction)} />
          ) : profile ? (
            <CandidateProfilePanel profile={profile} />
          ) : (
            <section className="card empty-state">
              <span className="empty-illustration" aria-hidden="true">
                <svg viewBox="0 0 80 80">
                  <rect height="56" rx="8" width="44" x="18" y="12" />
                  <path d="M29 29h22M29 39h22M29 49h14" />
                  <circle cx="59" cy="58" r="12" />
                  <path d="M59 52v12M53 58h12" />
                </svg>
              </span>
              <h2>Your profile preview will appear here</h2>
              <p>Upload a resume and parse it to see structured evidence, skills, and strengths.</p>
            </section>
          )}
        </aside>
      </div>

      {directions.length ? (
        <CareerDirectionCards
          directions={directions}
          onSelect={(direction) => {
            setSelectedDirection(direction);
            setSuggestions(null);
          }}
          selected={selectedDirection}
        />
      ) : null}

      {suggestions ? <SuggestionPanel result={suggestions} /> : null}

      <JobMatchPanel
        disabled={!profile}
        error={jobError}
        isLoading={jobLoading}
        jobProfile={jobProfile}
        matchResult={matchResult}
        onRunMatch={handleJobMatch}
      />
    </main>
  );
}

function messageFrom(cause: unknown): string {
  return cause instanceof Error ? cause.message : "An unexpected error occurred.";
}

function loadingLabel(action: Exclude<MainAction, null>): string {
  const labels = {
    upload: "Extracting resume text…",
    profile: "Structuring your candidate evidence…",
    directions: "Ranking evidence-supported career directions…",
    suggestions: "Generating and validating resume improvements…",
  };
  return labels[action];
}
