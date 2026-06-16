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
    <section className="card">
      <div className="card-heading">
        <div>
          <span className="eyebrow">Recommended paths</span>
          <h2>Your strongest career directions</h2>
          <p>Ranked from the evidence already present in your resume.</p>
        </div>
      </div>
      {error ? <ErrorMessage message={error} /> : null}
      {isLoading ? (
        <LoadingState
          compact={directions.length > 0}
          detail="This may take up to 60 seconds."
          label="Recommending career directions..."
        />
      ) : null}
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
                <span className="direction-meta">
                  <span className={`fit-badge fit-badge--${direction.fit_type}`}>
                    {direction.fit_type}
                  </span>
                  {direction.confidence_level} confidence
                </span>
              </span>
              <span className="score-ring" style={{ "--score": direction.score_midpoint } as React.CSSProperties}>
                <strong>{direction.score_midpoint}</strong>
                <small>fit</small>
              </span>
            </button>
          );
        })}
      </div>
      {selected ? (
        <div className="selection-detail">
          <div>
            <h3>Why this direction fits</h3>
            <ul className="clean-list">
              {selected.strengths_for_this_direction.slice(0, 3).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div>
            <h3>Current gaps</h3>
            {selected.gaps_for_this_direction.length ? (
              <ul className="clean-list clean-list--warning">
                {selected.gaps_for_this_direction.slice(0, 3).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="empty-copy">No material gaps identified.</p>
            )}
          </div>
        </div>
      ) : null}
    </section>
  );
}
