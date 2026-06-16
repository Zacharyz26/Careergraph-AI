"use client";

import { useState } from "react";

import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingState } from "@/components/ui/LoadingState";
import type { JobProfile, MatchResult } from "@/lib/types";

type JobMatchPanelProps = {
  disabled: boolean;
  jobProfile: JobProfile | null;
  matchResult: MatchResult | null;
  isLoading: boolean;
  error: string | null;
  onRunMatch: (description: string) => void;
};

export function JobMatchPanel({
  disabled,
  jobProfile,
  matchResult,
  isLoading,
  error,
  onRunMatch,
}: JobMatchPanelProps) {
  const [description, setDescription] = useState("");

  return (
    <section className="card job-match-card">
      <div className="card-heading">
        <div>
          <span className="eyebrow">Optional workflow</span>
          <h2>Check a specific job</h2>
          <p>Paste a job description to parse its requirements and score your fit.</p>
        </div>
        <span className="optional-badge">Optional</span>
      </div>

      <label className="field-label" htmlFor="job-description">
        Job description
      </label>
      <textarea
        disabled={disabled || isLoading}
        id="job-description"
        onChange={(event) => setDescription(event.target.value)}
        placeholder="Paste the full job description here…"
        rows={9}
        value={description}
      />
      <div className="field-footer">
        <span>{description.length.toLocaleString()} characters</span>
        <button
          className="button button--primary"
          disabled={disabled || isLoading || description.trim().length < 20}
          onClick={() => onRunMatch(description.trim())}
          type="button"
        >
          {isLoading ? "Analyzing job…" : "Parse & score match"}
        </button>
      </div>

      {disabled ? (
        <p className="inline-note">Complete candidate profile parsing before scoring a job.</p>
      ) : null}
      {error ? <ErrorMessage message={error} /> : null}
      {isLoading ? (
        <LoadingState
          compact={matchResult !== null}
          detail="This may take up to 60 seconds. Any previous match remains visible below."
          label="Parsing the job and calculating evidence coverage..."
          stages={[
            "Extracting required skills, responsibilities, and qualifications.",
            "Matching each requirement to existing candidate evidence.",
            "Calculating coverage, risk penalties, and explanation.",
          ]}
        />
      ) : null}

      {matchResult ? (
        <div className="match-result">
          <div className="match-score-block">
            <div className={`match-score match-score--${scoreTone(matchResult.final_score)}`}>
              <strong>{matchResult.final_score}</strong>
              <span>/ 100</span>
            </div>
            <div>
              <span className="eyebrow">{jobProfile?.job_title || "Parsed job"}</span>
              <h3>{matchResult.recommendation}</h3>
              <p>{matchResult.explanation}</p>
            </div>
          </div>

          <div className="score-breakdown">
            <ScoreBar label="Required coverage" value={matchResult.required_coverage_score} />
            <ScoreBar label="Responsibilities" value={matchResult.responsibility_alignment_score} />
            <ScoreBar label="Education fit" value={matchResult.education_fit_score} />
            <ScoreBar label="Evidence strength" value={matchResult.evidence_strength_score} />
          </div>

          <div className="match-columns">
            <div>
              <h4>Matched requirements</h4>
              <div className="tag-list">
                {[...matchResult.matched_required_skills, ...matchResult.matched_preferred_skills].map(
                  (skill) => <span className="tag tag--success" key={skill}>{skill}</span>,
                )}
              </div>
            </div>
            <div>
              <h4>Missing evidence</h4>
              <div className="tag-list">
                {[...matchResult.missing_required_skills, ...matchResult.missing_preferred_skills].map(
                  (skill) => <span className="tag tag--warning" key={skill}>{skill}</span>,
                )}
              </div>
            </div>
          </div>

          <details className="disclosure">
            <summary>View requirement-level analysis</summary>
            <div className="requirement-list">
              {matchResult.requirement_matches.map((item, index) => (
                <div className="requirement-row" key={`${item.requirement}-${index}`}>
                  <span className={`match-status match-status--${item.match_status}`}>
                    {item.match_status.replaceAll("_", " ")}
                  </span>
                  <div>
                    <strong>{item.requirement}</strong>
                    <p>{item.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </details>
        </div>
      ) : null}
    </section>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-bar">
      <div><span>{label}</span><strong>{value}%</strong></div>
      <span className="score-track"><span style={{ width: `${value}%` }} /></span>
    </div>
  );
}

function scoreTone(score: number) {
  if (score >= 80) return "strong";
  if (score >= 65) return "good";
  if (score >= 50) return "partial";
  return "low";
}
