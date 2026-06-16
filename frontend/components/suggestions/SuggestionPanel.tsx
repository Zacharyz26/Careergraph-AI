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
          <span className="eyebrow">Resume improvements</span>
          <h2>Evidence-grounded suggestions</h2>
          <p>
            {result?.overall_summary ??
              "Suggestions use only facts already supported by your resume."}
          </p>
        </div>
        {result ? (
          <span className="status-badge">{result.suggestions.length} suggestions</span>
        ) : null}
      </div>

      {error ? <ErrorMessage message={error} /> : null}
      {isLoading ? (
        <LoadingState
          compact={result !== null}
          detail="This may take up to 60 seconds."
          label="Generating evidence-grounded suggestions..."
        />
      ) : null}

      {result?.suggested_resume_focus.length ? (
        <div className="focus-banner">
          <strong>Recommended focus</strong>
          <span>{result.suggested_resume_focus.join(" · ")}</span>
        </div>
      ) : null}

      <div className="suggestion-list">
        {result?.suggestions.map((suggestion, index) => (
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
              {suggestion.should_add_to_resume
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
            <div className="evidence-line">
              <span aria-hidden="true">✓</span>
              Traced to {suggestion.source_evidence_ids.length} resume evidence item
              {suggestion.source_evidence_ids.length === 1 ? "" : "s"}
            </div>
          </article>
        ))}
      </div>

      {result?.missing_but_not_addable.length ? (
        <div className="unsupported-gaps">
          <h3>Needs new evidence or user input</h3>
          <p className="empty-copy">
            These items are intentionally excluded from suggested resume text.
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
