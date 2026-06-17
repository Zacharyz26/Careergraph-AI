import type { ReactNode } from "react";

import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingState } from "@/components/ui/LoadingState";
import type { SuggestionResponse } from "@/lib/types";

export function SuggestionPanel({
  result,
  isLoading = false,
  error = null,
}: {
  result: SuggestionResponse | null;
  isLoading?: boolean;
  error?: string | null;
}) {
  const strongestEvidence = result ? collectEvidence(result).slice(0, 5) : [];
  const priorityGaps = result
    ? [...result.evidence_gaps].sort((left, right) => priorityRank(left.priority) - priorityRank(right.priority))
    : [];

  return (
    <section className="card advisor-card">
      <div className="card-heading advisor-card-heading">
        <div>
          <span className="eyebrow">Advisor plan</span>
          <h2>Career positioning guidance</h2>
          <p>
            {result?.overall_summary ??
              "Get advisor-style guidance separated into evidence, readiness gaps, resume-ready changes, and next actions."}
          </p>
        </div>
        {result ? (
          <span className="status-badge">{advisorItemCount(result)} guidance items</span>
        ) : null}
      </div>

      {error ? <ErrorMessage message={error} /> : null}
      {isLoading ? (
        <LoadingState
          compact={result !== null}
          detail="This may take up to 60 seconds."
          label="Preparing advisor guidance..."
          stages={[
            "Reviewing strengths and target-direction gaps.",
            "Separating resume-ready wording from evidence to build next.",
            "Prioritizing practical changes and development actions.",
          ]}
        />
      ) : null}

      {result ? (
        <div className="advisor-summary-grid">
          <AdvisorMetric value={result.resume_ready_improvements.length} label="Resume-ready changes" />
          <AdvisorMetric value={priorityGaps.length} label="Readiness gaps" />
          <AdvisorMetric value={result.recommended_next_actions.length} label="Next actions" />
        </div>
      ) : null}

      {strongestEvidence.length ? (
        <AdvisorSection
          eyebrow="Strongest evidence"
          title="Proof points already present in the resume"
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
          eyebrow="Readiness gaps"
          title="Highest-priority evidence to build before claiming"
        >
          <div className="suggestion-list suggestion-list--two-column">
            {priorityGaps.map((gap) => (
              <article className="suggestion-item suggestion-item--warning" key={gap.gap}>
                <div className="suggestion-topline">
                  <span className="suggestion-type">{formatLabel(gap.category)}</span>
                  <span className={`risk-badge risk-badge--${priorityTone(gap.priority)}`}>
                    {gap.priority} priority
                  </span>
                </div>
                <h3>{gap.gap}</h3>
                <p className="suggestion-reason">{gap.why_it_matters}</p>
                <p className="suggested-copy">
                  <strong>Evidence to build:</strong> {gap.evidence_needed}
                </p>
              </article>
            ))}
          </div>
        </AdvisorSection>
      ) : null}

      {result?.resume_ready_improvements.length ? (
        <AdvisorSection
          eyebrow="Resume-ready improvements"
          title="Safe changes based on current evidence"
        >
          {result.resume_ready_improvements.map((suggestion, index) => (
            <article className="suggestion-item suggestion-item--resume" key={`${suggestion.suggestion_type}-${index}`}>
              <div className="suggestion-topline">
                <span className="suggestion-type">{formatLabel(suggestion.suggestion_type)}</span>
                <span className={`risk-badge risk-badge--${suggestion.risk_level}`}>
                  {suggestion.risk_level} risk
                </span>
              </div>
              <span className="suggestion-use">
                {suggestion.quality_level} value · {suggestion.should_add_to_resume
                  ? "Resume wording to review"
                  : "Positioning note"}
              </span>
              <h3>{suggestion.target_section}</h3>
              {suggestion.original_text &&
              suggestion.original_text !== suggestion.suggested_text ? (
                <div className="rewrite-comparison">
                  <div>
                    <span>Current</span>
                    <p>{suggestion.original_text}</p>
                  </div>
                  <div>
                    <span>Advisor draft</span>
                    <p>{suggestion.suggested_text}</p>
                  </div>
                </div>
              ) : (
                <p className="suggested-copy">{suggestion.suggested_text}</p>
              )}
              <p className="suggestion-reason">{suggestion.reason}</p>
              <EvidenceLine count={suggestion.source_evidence_ids.length} />
            </article>
          ))}
        </AdvisorSection>
      ) : null}

      {result?.positioning_advice.length ? (
        <AdvisorSection
          eyebrow="Positioning"
          title="How to emphasize existing strengths"
        >
          <div className="suggestion-list suggestion-list--two-column">
            {result.positioning_advice.map((item, index) => (
              <article className="suggestion-item" key={`${item.target_section}-${index}`}>
                <div className="suggestion-topline">
                  <span className="suggestion-type">{item.target_section}</span>
                  <span className={`risk-badge risk-badge--${qualityTone(item.quality_level)}`}>
                    {item.quality_level} value
                  </span>
                </div>
                <h3>{item.advice}</h3>
                <p className="suggestion-reason">{item.reason}</p>
                <EvidenceLine count={item.source_evidence_ids.length} />
              </article>
            ))}
          </div>
        </AdvisorSection>
      ) : null}

      {result?.recommended_next_actions.length ? (
        <AdvisorSection eyebrow="Next actions" title="Practical ways to strengthen the profile">
          <div className="action-timeline">
            {result.recommended_next_actions.map((action) => (
              <article className="timeline-item" key={action.action}>
                <div className="timeline-marker" aria-hidden="true" />
                <div>
                  <div className="suggestion-topline">
                    <span className="suggestion-type">{action.priority} priority</span>
                    <span className={`risk-badge risk-badge--${qualityTone(action.quality_level)}`}>
                      {action.quality_level} value
                    </span>
                  </div>
                  <h3>{action.action}</h3>
                  <p className="suggestion-reason">{action.rationale}</p>
                  {action.target_gap ? (
                    <p className="suggested-copy">
                      <strong>Targets:</strong> {action.target_gap}
                    </p>
                  ) : null}
                  {action.suggested_artifact ? (
                    <p className="suggested-copy">
                      <strong>Useful artifact:</strong> {action.suggested_artifact}
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
          <h3>Evidence to build next</h3>
          <p className="empty-copy">
            Useful signals to develop before presenting them as resume strengths.
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
          <summary>View advisor guardrails</summary>
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

function EvidenceLine({ count }: { count: number }) {
  return (
    <div className="evidence-line">
      <span aria-hidden="true">✓</span>
      Traced to {count} resume evidence item{count === 1 ? "" : "s"}
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

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
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
