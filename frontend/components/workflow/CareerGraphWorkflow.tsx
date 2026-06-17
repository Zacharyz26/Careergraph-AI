"use client";

import { useId, useState } from "react";

import { CareerDirectionCards } from "@/components/career/CareerDirectionCards";
import { JobMatchPanel } from "@/components/match/JobMatchPanel";
import { CandidateProfilePanel } from "@/components/resume/CandidateProfilePanel";
import { ResumeUploader } from "@/components/resume/ResumeUploader";
import { SuggestionPanel } from "@/components/suggestions/SuggestionPanel";
import { LoadingState } from "@/components/ui/LoadingState";
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
  const replaceInputId = useId();
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

  const isAnalyzing = profileLoading || directionsLoading;
  const analysisStatus = isAnalyzing
    ? "Analyzing resume evidence"
    : directions.length
      ? "Directions ready"
      : profile
        ? "Profile ready"
        : upload
          ? "Resume prepared"
          : "Ready for resume";

  async function handleUpload(file: File) {
    setUploadLoading(true);
    setProfileLoading(false);
    setDirectionsLoading(false);
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

  async function handleAnalyzeResume() {
    if (!upload) return;
    let stage: "profile" | "directions" = "profile";
    setProfileLoading(true);
    setProfileError(null);
    setDirections([]);
    setSelectedDirection(null);
    setSuggestions(null);
    setDirectionsError(null);
    setSuggestionsError(null);
    try {
      const parsedProfile = await parseCandidateProfile(upload.extracted_text);
      setProfile(parsedProfile);
      setProfileLoading(false);

      stage = "directions";
      setDirectionsLoading(true);
      const result = await recommendCareerDirections(parsedProfile);
      setDirections(result.directions);
      setSelectedDirection(result.directions[0] ?? null);
    } catch (cause) {
      if (stage === "profile") {
        setProfileError(messageFrom(cause));
      } else {
        setDirectionsError(messageFrom(cause));
      }
    } finally {
      setProfileLoading(false);
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

  if (!upload) {
    return (
      <main className="career-console career-console--empty">
        <section className="console-intake">
          <div className="console-intake__copy">
            <span className="hero-kicker">AI career advisor workspace</span>
            <h1>Turn a resume into a career direction brief.</h1>
            <p>
              Upload a PDF or DOCX resume, then CareerGraph prepares evidence-backed
              profile signals, recommended directions, and advisor guidance.
            </p>
          </div>
          <ResumeUploader
            error={uploadError}
            isLoading={uploadLoading}
            onUpload={handleUpload}
            upload={upload}
          />
        </section>
      </main>
    );
  }

  return (
    <main className="career-console">
      <header className="console-header">
        <div>
          <span className="hero-kicker">CareerGraph AI</span>
          <h1>{profile?.basic_info.full_name || "Career direction workspace"}</h1>
          <p>{uploadError ?? "Evidence-grounded career direction and resume guidance"}</p>
        </div>
        <div className="console-header__actions">
          <div className="console-file-pill">
            <span className="file-type-icon">{upload.file_type.toUpperCase()}</span>
            <span>{upload.filename}</span>
            <label className="file-replace-button" htmlFor={replaceInputId}>
              Replace
              <input
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                disabled={uploadLoading || isAnalyzing}
                id={replaceInputId}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void handleUpload(file);
                  event.target.value = "";
                }}
                type="file"
              />
            </label>
          </div>
          <span className="console-status">{analysisStatus}</span>
          <button
            className="button button--dark"
            disabled={isAnalyzing || uploadLoading}
            onClick={handleAnalyzeResume}
            type="button"
          >
            {isAnalyzing ? "Analyzing..." : profile ? "Refresh analysis" : "Analyze resume"}
          </button>
        </div>
      </header>

      <section className="console-workbench">
        <section className="console-main">
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
          ) : (
            <section className="console-analysis-panel">
              <span className="eyebrow">Career fit</span>
              <h2>{isAnalyzing ? "Building your career direction brief" : "Ready to map career directions"}</h2>
              <p>
                CareerGraph builds an evidence profile first, then ranks realistic career
                directions by fit, confidence, and readiness gaps.
              </p>
              {isAnalyzing ? (
                <LoadingState
                  compact
                  label="Analyzing resume evidence..."
                  stages={[
                    "Building evidence profile.",
                    "Comparing evidence against career paths.",
                    "Preparing ranked direction hypotheses.",
                  ]}
                />
              ) : (
                <button
                  className="button button--primary"
                  onClick={handleAnalyzeResume}
                  type="button"
                >
                  Analyze resume
                </button>
              )}
              {profileError || directionsError ? (
                <p className="upload-error" role="alert">{profileError ?? directionsError}</p>
              ) : null}
            </section>
          )}
        </section>

        <aside className="console-inspector">
          {profile || profileLoading || profileError ? (
            <CandidateProfilePanel
              compact
              error={profileError}
              isLoading={profileLoading}
              profile={profile}
            />
          ) : (
            <section className="inspector-empty">
              <span className="eyebrow">Evidence profile</span>
              <h2>Profile summary</h2>
              <p>Analysis will surface skills, strengths, and resume evidence here.</p>
            </section>
          )}

          <section className="advisor-cta-card">
            <span className="eyebrow">Advisor plan</span>
            <h2>{selectedDirection ? "Selected direction guidance" : "Select a direction"}</h2>
            <p>
              {selectedDirection
                ? `Prepare resume-ready improvements and next actions for ${selectedDirection.direction}.`
                : "Recommended directions will unlock focused advisor guidance."}
            </p>
            {selectedDirection ? (
              <button
                className="button button--dark button--wide"
                disabled={suggestionsLoading}
                onClick={handleSuggestions}
                type="button"
              >
                {suggestionsLoading ? "Preparing..." : suggestions ? "Refresh advisor" : "Prepare advisor"}
              </button>
            ) : null}
          </section>
        </aside>
      </section>

      <section className="console-secondary">
        {suggestions || suggestionsLoading || suggestionsError ? (
          <SuggestionPanel
            error={suggestionsError}
            isLoading={suggestionsLoading}
            result={suggestions}
          />
        ) : null}

        {profile ? (
          <JobMatchPanel
            disabled={!profile}
            error={jobError}
            isLoading={jobLoading}
            jobProfile={jobProfile}
            matchResult={matchResult}
            onRunMatch={handleJobMatch}
          />
        ) : null}
      </section>
    </main>
  );
}

function messageFrom(cause: unknown): string {
  return cause instanceof Error ? cause.message : "An unexpected error occurred.";
}
