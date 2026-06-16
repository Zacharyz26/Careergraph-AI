"use client";

import { useMemo, useState } from "react";

import { CareerDirectionCards } from "@/components/career/CareerDirectionCards";
import { JobMatchPanel } from "@/components/match/JobMatchPanel";
import { CandidateProfilePanel } from "@/components/resume/CandidateProfilePanel";
import { ResumeUploader } from "@/components/resume/ResumeUploader";
import { SuggestionPanel } from "@/components/suggestions/SuggestionPanel";
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

export function CareerGraphWorkflow() {
  const [upload, setUpload] = useState<ResumeUploadResponse | null>(null);
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [directions, setDirections] = useState<CareerDirection[]>([]);
  const [selectedDirection, setSelectedDirection] = useState<CareerDirection | null>(null);
  const [suggestions, setSuggestions] = useState<SuggestionResponse | null>(null);
  const [jobProfile, setJobProfile] = useState<JobProfile | null>(null);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [directionsLoading, setDirectionsLoading] = useState(false);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [jobLoading, setJobLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [directionsError, setDirectionsError] = useState<string | null>(null);
  const [suggestionsError, setSuggestionsError] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);

  const currentStep = useMemo(() => {
    if (matchResult) return 5;
    if (suggestions) return 4;
    if (directions.length) return 3;
    if (profile) return 2;
    return 1;
  }, [directions.length, matchResult, profile, suggestions]);

  async function handleUpload(file: File) {
    setUploadLoading(true);
    setUploadError(null);
    setUpload(null);
    setProfile(null);
    setDirections([]);
    setSelectedDirection(null);
    setSuggestions(null);
    setJobProfile(null);
    setMatchResult(null);
    setProfileError(null);
    setDirectionsError(null);
    setSuggestionsError(null);
    setJobError(null);
    try {
      setUpload(await uploadResume(file));
    } catch (cause) {
      setUploadError(messageFrom(cause));
    } finally {
      setUploadLoading(false);
    }
  }

  async function handleParseProfile() {
    if (!upload) return;
    setProfileLoading(true);
    setProfileError(null);
    try {
      setProfile(await parseCandidateProfile(upload.extracted_text));
    } catch (cause) {
      setProfileError(messageFrom(cause));
    } finally {
      setProfileLoading(false);
    }
  }

  async function handleDirections() {
    if (!profile) return;
    setDirectionsLoading(true);
    setDirectionsError(null);
    try {
      const result = await recommendCareerDirections(profile);
      setDirections(result.directions);
      setSelectedDirection(result.directions[0] ?? null);
      setSuggestions(null);
      setSuggestionsError(null);
    } catch (cause) {
      setDirectionsError(messageFrom(cause));
    } finally {
      setDirectionsLoading(false);
    }
  }

  async function handleSuggestions() {
    if (!profile || !selectedDirection) return;
    setSuggestionsLoading(true);
    setSuggestionsError(null);
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
      setSuggestionsError(messageFrom(cause));
    } finally {
      setSuggestionsLoading(false);
    }
  }

  async function handleJobMatch(description: string) {
    if (!profile) return;
    setJobLoading(true);
    setJobError(null);
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

      <div className="workflow-grid">
        <div className="workflow-controls">
          <ResumeUploader
            error={uploadError}
            isLoading={uploadLoading}
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
                disabled={profileLoading}
                onClick={handleParseProfile}
                type="button"
              >
                {profileLoading ? "Parsing profile…" : profile ? "Rebuild profile" : "Parse candidate profile"}
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
                disabled={directionsLoading}
                onClick={handleDirections}
                type="button"
              >
                {directionsLoading ? "Ranking directions…" : directions.length ? "Refresh directions" : "Recommend career directions"}
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
                disabled={suggestionsLoading}
                onClick={handleSuggestions}
                type="button"
              >
                {suggestionsLoading ? "Generating suggestions…" : suggestions ? "Refresh improvement suggestions" : "Generate improvement suggestions"}
              </button>
            </section>
          ) : null}
        </div>

        <aside className="workflow-results">
          {profile || profileLoading || profileError ? (
            <CandidateProfilePanel
              error={profileError}
              isLoading={profileLoading}
              profile={profile}
            />
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

      {directions.length || directionsLoading || directionsError ? (
        <CareerDirectionCards
          directions={directions}
          error={directionsError}
          isLoading={directionsLoading}
          onSelect={(direction) => {
            setSelectedDirection(direction);
            setSuggestions(null);
            setSuggestionsError(null);
          }}
          selected={selectedDirection}
        />
      ) : null}

      {suggestions || suggestionsLoading || suggestionsError ? (
        <SuggestionPanel
          error={suggestionsError}
          isLoading={suggestionsLoading}
          result={suggestions}
        />
      ) : null}

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
