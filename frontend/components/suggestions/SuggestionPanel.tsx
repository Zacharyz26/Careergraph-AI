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
  return (
    <section className="card">
      <div className="card-heading">
        <div>
          <span className="eyebrow">Resume positioning</span>
          <h2>Resume Positioning & Career Gap Advisor</h2>
          <p>
            {result?.overall_summary ??
              "Get resume-ready improvements, positioning advice, evidence gaps, and next actions."}
          </p>
        </div>
        {result ? (
          <span className="status-badge">
            {advisorItemCount(result)} advisor items
          </span>
        ) : null}
      </div>

      {error ? <ErrorMessage message={error} /> : null}
      {isLoading ? (
        <LoadingState
          compact={result !== null}
          detail="This may take up to 60 seconds."
          label="Generating resume positioning and gap advice..."
          stages={[
            "Reviewing strongest proof points and target-role gaps.",
            "Separating updates you can make now from experience to build next.",
            "Prioritizing high-value development areas and next actions.",
          ]}
        />
      ) : null}

      {result?.positioning_advice.length ? (
        <AdvisorSection
          eyebrow="Positioning advice"
          title="How to emphasize existing evidence"
        >
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
        </AdvisorSection>
      ) : null}

      {result?.resume_ready_improvements.length ? (
        <AdvisorSection
          eyebrow="Resume-ready"
          title="Safe wording based only on current evidence"
        >
          {result.resume_ready_improvements.map((suggestion, index) => (
            <article className="suggestion-item" key={`${suggestion.suggestion_type}-${index}`}>
              <div className="suggestion-topline">
                <span className="suggestion-type">
                  {suggestion.suggestion_type.replaceAll("_", " ")}
                </span>
                <span className={`risk-badge risk-badge--${suggestion.risk_level}`}>
                  {suggestion.risk_level} risk
                </span>
              </div>
              <span className="suggestion-use">
                {suggestion.quality_level} value · {suggestion.should_add_to_resume
                  ? "Candidate wording for review"
                  : "Positioning action, not resume-ready text"}
              </span>
              <h3>{suggestion.target_section}</h3>
              {suggestion.original_text &&
              suggestion.original_text !== suggestion.suggested_text ? (
                <div className="rewrite-comparison">
                  <div>
                    <span>Original</span>
                    <p>{suggestion.original_text}</p>
                  </div>
                  <div>
                    <span>Suggested</span>
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

      {result?.evidence_gaps.length ? (
        <AdvisorSection eyebrow="Growth areas" title="Proof points to strengthen for this direction">
          {result.evidence_gaps.map((gap) => (
            <article className="suggestion-item suggestion-item--warning" key={gap.gap}>
              <div className="suggestion-topline">
                <span className="suggestion-type">
                  {gap.category.replaceAll("_", " ")}
                </span>
                <span className={`risk-badge risk-badge--${priorityTone(gap.priority)}`}>
                  {gap.priority} priority
                </span>
              </div>
              <h3>{gap.gap}</h3>
              <p className="suggestion-reason">{gap.why_it_matters}</p>
              <p className="suggested-copy">{gap.evidence_needed}</p>
            </article>
          ))}
        </AdvisorSection>
      ) : null}

      {result?.recommended_next_actions.length ? (
        <AdvisorSection eyebrow="Next actions" title="Practical ways to strengthen your profile">
          {result.recommended_next_actions.map((action) => (
            <article className="suggestion-item" key={action.action}>
              <div className="suggestion-topline">
                <span className="suggestion-type">{action.priority} priority</span>
                <span className={`risk-badge risk-badge--${qualityTone(action.quality_level)}`}>
                  {action.quality_level} value
                </span>
              </div>
              <h3>{action.action}</h3>
              <p className="suggestion-reason">{action.rationale}</p>
              {action.target_gap ? (
                <p className="suggested-copy">Target gap: {action.target_gap}</p>
              ) : null}
              {action.suggested_artifact ? (
                <p className="suggested-copy">
                  Useful artifact: {action.suggested_artifact}
                </p>
              ) : null}
            </article>
          ))}
        </AdvisorSection>
      ) : null}

      {result?.missing_but_not_addable.length ? (
        <div className="unsupported-gaps">
          <h3>Future positioning opportunities</h3>
          <p className="empty-copy">
            These are useful signals to develop before presenting them as resume strengths.
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
          <summary>View suggestion safety checks</summary>
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
  children: React.ReactNode;
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
