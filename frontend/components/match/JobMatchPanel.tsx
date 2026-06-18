"use client";

import { useState } from "react";

import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  formatCopy,
  matchRecommendationLabels,
  matchStatusLabels,
  type PreferredLanguage,
  uiCopy,
} from "@/lib/i18n";
import type { JobProfile, MatchResult } from "@/lib/types";

type JobMatchPanelProps = {
  disabled: boolean;
  jobProfile: JobProfile | null;
  matchResult: MatchResult | null;
  isLoading: boolean;
  error: string | null;
  onRunMatch: (description: string) => void;
  language?: PreferredLanguage;
};

export function JobMatchPanel({
  disabled,
  jobProfile,
  matchResult,
  isLoading,
  error,
  onRunMatch,
  language = "en",
}: JobMatchPanelProps) {
  const t = uiCopy[language];
  const [description, setDescription] = useState("");

  return (
    <section className="card job-match-card">
      <details className="job-match-disclosure" open={Boolean(matchResult || error || isLoading)}>
        <summary>
          <span>
            <span className="eyebrow">{t.optionalJobFit}</span>
            <strong>{t.compareRole}</strong>
          </span>
          <span className="optional-badge">{t.optional}</span>
        </summary>

        <div className="job-match-body">
          <p className="inline-note">{t.jobFitBody}</p>
          <label className="field-label" htmlFor="job-description">
            {t.jobDescription}
          </label>
          <textarea
            disabled={disabled || isLoading}
            id="job-description"
            onChange={(event) => setDescription(event.target.value)}
            placeholder={t.jobPlaceholder}
            rows={7}
            value={description}
          />
          <div className="field-footer">
            <span>
              {formatCopy(t.characters, {
                count: description.length.toLocaleString(),
              })}
            </span>
            <button
              className="button button--primary"
              disabled={disabled || isLoading || description.trim().length < 20}
              onClick={() => onRunMatch(description.trim())}
              type="button"
            >
              {isLoading ? t.checkingRoleFit : t.checkRoleFit}
            </button>
          </div>

          {disabled ? (
            <p className="inline-note">{t.buildProfileFirst}</p>
          ) : null}
          {error ? <ErrorMessage message={error} title={t.errorTitle} /> : null}
          {isLoading ? (
            <LoadingState
              compact={matchResult !== null}
              detail={t.jobLoadingDetail}
              label={t.jobLoadingLabel}
              stages={[...t.jobLoadingStages]}
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
                  <span className="eyebrow">{jobProfile?.job_title || t.parsedJob}</span>
                  <h3>{matchRecommendationLabels[language][matchResult.recommendation]}</h3>
                  <p>{matchResult.explanation}</p>
                </div>
              </div>

              <div className="score-breakdown">
                <ScoreBar label={t.requiredCoverage} value={matchResult.required_coverage_score} />
                <ScoreBar label={t.responsibilities} value={matchResult.responsibility_alignment_score} />
                <ScoreBar label={t.educationFit} value={matchResult.education_fit_score} />
                <ScoreBar label={t.evidenceStrength} value={matchResult.evidence_strength_score} />
              </div>

              <div className="match-columns">
                <div>
                  <h4>{t.matchedRequirements}</h4>
                  <div className="tag-list">
                    {[...matchResult.matched_required_skills, ...matchResult.matched_preferred_skills].map(
                      (skill) => <span className="tag tag--success" key={skill}>{skill}</span>,
                    )}
                  </div>
                </div>
                <div>
                  <h4>{t.missingEvidence}</h4>
                  <div className="tag-list">
                    {[...matchResult.missing_required_skills, ...matchResult.missing_preferred_skills].map(
                      (skill) => <span className="tag tag--warning" key={skill}>{skill}</span>,
                    )}
                  </div>
                </div>
              </div>

              <details className="disclosure">
                <summary>{t.viewRequirementAnalysis}</summary>
                <div className="requirement-list">
                  {matchResult.requirement_matches.map((item, index) => (
                    <div className="requirement-row" key={`${item.requirement}-${index}`}>
                      <span className={`match-status match-status--${item.match_status}`}>
                        {matchStatusLabels[language][item.match_status]}
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
        </div>
      </details>
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
