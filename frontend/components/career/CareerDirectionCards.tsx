import type { CSSProperties, ReactNode } from "react";

import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingState } from "@/components/ui/LoadingState";
import type { CareerDirection } from "@/lib/types";

type CareerDirectionCardsProps = {
  directions: CareerDirection[];
  selected: CareerDirection | null;
  onSelect: (direction: CareerDirection) => void;
  isLoading?: boolean;
  error?: string | null;
};

export function CareerDirectionCards({
  directions,
  selected,
  onSelect,
  isLoading = false,
  error = null,
}: CareerDirectionCardsProps) {
  return (
    <section className="card direction-workspace">
      <div className="card-heading">
        <div>
          <span className="eyebrow">Career fit</span>
          <h2>Recommended career directions</h2>
          <p>Ranked by resume evidence, role-family fit, confidence, and readiness gaps.</p>
        </div>
        {directions.length ? (
          <span className="status-badge">{directions.length} hypotheses</span>
        ) : null}
      </div>

      {error ? <ErrorMessage message={error} /> : null}
      {isLoading ? (
        <LoadingState
          compact={directions.length > 0}
          detail="This may take up to 60 seconds."
          label="Mapping career direction hypotheses..."
          stages={[
            "Comparing resume evidence against role families.",
            "Checking strength, directness, and source diversity.",
            "Ranking directions by fit, readiness, and confidence.",
          ]}
        />
      ) : null}

      <div className="direction-layout">
        <div className="direction-list">
          {directions.map((direction) => {
            const isSelected = selected?.direction === direction.direction;
            return (
              <button
                aria-pressed={isSelected}
                className={`direction-card${isSelected ? " direction-card--selected" : ""}`}
                key={`${direction.rank}-${direction.direction}`}
                onClick={() => onSelect(direction)}
                type="button"
              >
                <span className="direction-rank">{direction.rank}</span>
                <span className="direction-copy">
                  <strong>{direction.direction}</strong>
                  <span>{direction.role_family} · {direction.seniority_level}</span>
                  <span className="direction-evidence-preview">
                    {direction.matched_evidence[0]?.text ?? "Evidence-supported direction"}
                  </span>
                  <span className="direction-meta">
                    <span className={`fit-badge fit-badge--${direction.fit_type}`}>
                      {friendlyFitType(direction.fit_type)}
                    </span>
                    {direction.confidence_level} confidence
                  </span>
                </span>
                <span className="score-ring" style={{ "--score": direction.score_midpoint } as CSSProperties}>
                  <strong>{direction.score_midpoint}</strong>
                  <small>fit</small>
                </span>
              </button>
            );
          })}
        </div>

        {selected ? (
          <aside className="selected-direction-panel">
            <div className="selected-direction-topline">
              <span className={`fit-badge fit-badge--${selected.fit_type}`}>
                {friendlyFitType(selected.fit_type)}
              </span>
              <span>{selected.confidence_level} confidence</span>
            </div>
            <h3>{selected.direction}</h3>
            <p>
              {selected.role_family} · {selected.seniority_level} · {selected.score_range_low}
              -{selected.score_range_high} fit range
            </p>

            <DirectionSection title="Why this fits">
              <ul className="clean-list">
                {selected.strengths_for_this_direction.slice(0, 4).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </DirectionSection>

            <DirectionSection title="Readiness gaps">
              {selected.gaps_for_this_direction.length ? (
                <ul className="clean-list clean-list--warning">
                  {selected.gaps_for_this_direction.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="empty-copy">No material gaps identified.</p>
              )}
            </DirectionSection>

            {selected.example_job_titles.length ? (
              <DirectionSection title="Example titles">
                <div className="tag-list">
                  {selected.example_job_titles.slice(0, 5).map((title) => (
                    <span className="tag tag--neutral" key={title}>{title}</span>
                  ))}
                </div>
              </DirectionSection>
            ) : null}
          </aside>
        ) : null}
      </div>
    </section>
  );
}

function DirectionSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="direction-detail-section">
      <h4>{title}</h4>
      {children}
    </section>
  );
}

function friendlyFitType(fitType: CareerDirection["fit_type"]) {
  return fitType.replaceAll("_", " ");
}
