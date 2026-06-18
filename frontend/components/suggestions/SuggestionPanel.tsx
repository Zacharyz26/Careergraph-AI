import type { ReactNode } from "react";

import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  evidenceGapCategoryLabels,
  formatCopy,
  priorityLabels,
  qualityLabels,
  riskLabels,
  suggestionTypeLabels,
  type PreferredLanguage,
  uiCopy,
} from "@/lib/i18n";
import type { SuggestionResponse } from "@/lib/types";

export function SuggestionPanel({
  result,
  isLoading = false,
  error = null,
  language = "en",
}: {
  result: SuggestionResponse | null;
  isLoading?: boolean;
  error?: string | null;
  language?: PreferredLanguage;
}) {
  const t = uiCopy[language];
  const strongestEvidence = result ? collectEvidence(result).slice(0, 5) : [];
  const priorityGaps = result
    ? [...result.evidence_gaps].sort((left, right) => priorityRank(left.priority) - priorityRank(right.priority))
    : [];

  return (
    <section className="card advisor-card">
      <div className="card-heading advisor-card-heading">
        <div>
          <span className="eyebrow">{t.advisorPlan}</span>
          <h2>{t.advisorGuidanceTitle}</h2>
          <p>
            {result?.overall_summary ??
              t.advisorEmptySummary}
          </p>
        </div>
        {result ? (
          <span className="status-badge">
            {formatCopy(t.guidanceItems, { count: advisorItemCount(result).toString() })}
          </span>
        ) : null}
      </div>

      {error ? <ErrorMessage message={error} title={t.errorTitle} /> : null}
      {isLoading ? (
        <LoadingState
          compact={result !== null}
          detail={t.loadingDetail}
          label={t.advisorLoadingLabel}
          stages={[...t.advisorLoadingStages]}
        />
      ) : null}

      {result ? (
        <div className="advisor-summary-grid">
          <AdvisorMetric value={result.resume_ready_improvements.length} label={t.resumeReadyChanges} />
          <AdvisorMetric value={priorityGaps.length} label={t.readinessGaps} />
          <AdvisorMetric value={result.recommended_next_actions.length} label={t.nextActions} />
        </div>
      ) : null}

      {strongestEvidence.length ? (
        <AdvisorSection
          eyebrow={t.strongestEvidence}
          title={t.strongestEvidenceTitle}
        >
          <div className="evidence-card-list">
            {strongestEvidence.map((item, index) => (
              <article className="evidence-card" key={`${item}-${index}`}>
                <span>{index + 1}</span>
                <p>{item}</p>
              </article>
            ))}
          </div>
        </AdvisorSection>
      ) : null}

      {priorityGaps.length ? (
        <AdvisorSection
          eyebrow={t.readinessGaps}
          title={t.readinessGapsTitle}
        >
          <div className="suggestion-list suggestion-list--two-column">
            {priorityGaps.map((gap) => (
              <article className="suggestion-item suggestion-item--warning" key={gap.gap}>
                <div className="suggestion-topline">
                  <span className="suggestion-type">{evidenceGapCategoryLabels[language][gap.category]}</span>
                  <span className={`risk-badge risk-badge--${priorityTone(gap.priority)}`}>
                    {priorityLabels[language][gap.priority]} {t.prioritySuffix}
                  </span>
                </div>
                <h3>{gap.gap}</h3>
                <p className="suggestion-reason">{gap.why_it_matters}</p>
                <p className="suggested-copy">
                  <strong>{t.evidenceToBuild}</strong> {gap.evidence_needed}
                </p>
              </article>
            ))}
          </div>
        </AdvisorSection>
      ) : null}

      {result?.resume_ready_improvements.length ? (
        <AdvisorSection
          eyebrow={t.resumeReadyImprovements}
          title={t.resumeReadyTitle}
        >
          {result.resume_ready_improvements.map((suggestion, index) => (
            <article className="suggestion-item suggestion-item--resume" key={`${suggestion.suggestion_type}-${index}`}>
              <div className="suggestion-topline">
                <span className="suggestion-type">
                  {suggestionTypeLabels[language][suggestion.suggestion_type]}
                </span>
                <span className={`risk-badge risk-badge--${suggestion.risk_level}`}>
                  {riskLabels[language][suggestion.risk_level]} {t.riskSuffix}
                </span>
              </div>
              <span className="suggestion-use">
                {qualityLabels[language][suggestion.quality_level]} {t.valueSuffix} · {suggestion.should_add_to_resume
                  ? t.resumeWordingReview
                  : t.positioningNote}
              </span>
              <h3>{suggestion.target_section}</h3>
              {suggestion.original_text &&
              suggestion.original_text !== suggestion.suggested_text ? (
                <div className="rewrite-comparison">
                  <div>
                    <span>{t.current}</span>
                    <p>{suggestion.original_text}</p>
                  </div>
                  <div>
                    <span>{t.advisorDraft}</span>
                    <p>{suggestion.suggested_text}</p>
                  </div>
                </div>
              ) : (
                <p className="suggested-copy">{suggestion.suggested_text}</p>
              )}
              <p className="suggestion-reason">{suggestion.reason}</p>
              <EvidenceLine count={suggestion.source_evidence_ids.length} language={language} />
            </article>
          ))}
        </AdvisorSection>
      ) : null}

      {result?.positioning_advice.length ? (
        <AdvisorSection
          eyebrow={t.positioning}
          title={t.positioningTitle}
        >
          <div className="suggestion-list suggestion-list--two-column">
            {result.positioning_advice.map((item, index) => (
              <article className="suggestion-item" key={`${item.target_section}-${index}`}>
                <div className="suggestion-topline">
                  <span className="suggestion-type">{item.target_section}</span>
                  <span className={`risk-badge risk-badge--${qualityTone(item.quality_level)}`}>
                    {qualityLabels[language][item.quality_level]} {t.valueSuffix}
                  </span>
                </div>
                <h3>{item.advice}</h3>
                <p className="suggestion-reason">{item.reason}</p>
                <EvidenceLine count={item.source_evidence_ids.length} language={language} />
              </article>
            ))}
          </div>
        </AdvisorSection>
      ) : null}

      {result?.recommended_next_actions.length ? (
        <AdvisorSection eyebrow={t.nextActions} title={t.nextActionsTitle}>
          <div className="action-timeline">
            {result.recommended_next_actions.map((action) => (
              <article className="timeline-item" key={action.action}>
                <div className="timeline-marker" aria-hidden="true" />
                <div>
                  <div className="suggestion-topline">
                    <span className="suggestion-type">
                      {priorityLabels[language][action.priority]} {t.prioritySuffix}
                    </span>
                    <span className={`risk-badge risk-badge--${qualityTone(action.quality_level)}`}>
                      {qualityLabels[language][action.quality_level]} {t.valueSuffix}
                    </span>
                  </div>
                  <h3>{action.action}</h3>
                  <p className="suggestion-reason">{action.rationale}</p>
                  {action.target_gap ? (
                    <p className="suggested-copy">
                      <strong>{t.targets}</strong> {action.target_gap}
                    </p>
                  ) : null}
                  {action.suggested_artifact ? (
                    <p className="suggested-copy">
                      <strong>{t.usefulArtifact}</strong> {action.suggested_artifact}
                    </p>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        </AdvisorSection>
      ) : null}

      {result?.missing_but_not_addable.length ? (
        <div className="unsupported-gaps">
          <h3>{t.evidenceToBuildNext}</h3>
          <p className="empty-copy">
            {t.evidenceToBuildNextBody}
          </p>
          <div className="tag-list">
            {result.missing_but_not_addable.map((gap) => (
              <span className="tag tag--warning" key={gap}>{gap}</span>
            ))}
          </div>
        </div>
      ) : null}

      {result?.warnings.length ? (
        <details className="disclosure">
          <summary>{t.viewAdvisorGuardrails}</summary>
          <ul className="clean-list clean-list--warning">
            {result.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}

function AdvisorSection({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="advisor-section">
      <div className="advisor-heading">
        <span className="eyebrow">{eyebrow}</span>
        <h3>{title}</h3>
      </div>
      <div className="suggestion-list">{children}</div>
    </section>
  );
}

function AdvisorMetric({ value, label }: { value: number; label: string }) {
  return (
    <div className="advisor-metric">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function EvidenceLine({
  count,
  language,
}: {
  count: number;
  language: PreferredLanguage;
}) {
  const t = uiCopy[language];
  return (
    <div className="evidence-line">
      <span aria-hidden="true">✓</span>
      {formatCopy(t.tracedToEvidence, {
        count: count.toString(),
        plural: count === 1 ? "" : "s",
      })}
    </div>
  );
}

function advisorItemCount(result: SuggestionResponse) {
  return (
    result.resume_ready_improvements.length +
    result.positioning_advice.length +
    result.evidence_gaps.length +
    result.recommended_next_actions.length
  );
}

function collectEvidence(result: SuggestionResponse) {
  const evidence = [
    ...result.resume_ready_improvements.flatMap((item) => item.source_evidence_text),
    ...result.positioning_advice.flatMap((item) => item.source_evidence_text),
  ];
  return [...new Set(evidence.filter(Boolean))];
}

function priorityRank(priority: "high" | "medium" | "low") {
  if (priority === "high") return 0;
  if (priority === "medium") return 1;
  return 2;
}

function qualityTone(level: "high" | "medium" | "low") {
  if (level === "high") return "low";
  if (level === "medium") return "medium";
  return "high";
}

function priorityTone(priority: "high" | "medium" | "low") {
  if (priority === "high") return "high";
  if (priority === "medium") return "medium";
  return "low";
}
