import type { CSSProperties, ReactNode } from "react";

import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingState } from "@/components/ui/LoadingState";
import {
  confidenceLabels,
  fitTypeLabels,
  formatCopy,
  type PreferredLanguage,
  uiCopy,
} from "@/lib/i18n";
import type { CareerDirection } from "@/lib/types";

type CareerDirectionCardsProps = {
  directions: CareerDirection[];
  selected: CareerDirection | null;
  onSelect: (direction: CareerDirection) => void;
  isLoading?: boolean;
  error?: string | null;
  language?: PreferredLanguage;
};

export function CareerDirectionCards({
  directions,
  selected,
  onSelect,
  isLoading = false,
  error = null,
  language = "en",
}: CareerDirectionCardsProps) {
  const t = uiCopy[language];
  return (
    <section className="card direction-workspace">
      <div className="card-heading">
        <div>
          <span className="eyebrow">{t.careerFit}</span>
          <h2>{t.directionsTitle}</h2>
          <p>{t.directionsSubtitle}</p>
        </div>
        {directions.length ? (
          <span className="status-badge">
            {formatCopy(t.hypotheses, { count: directions.length.toString() })}
          </span>
        ) : null}
      </div>

      {error ? <ErrorMessage message={error} title={t.errorTitle} /> : null}
      {isLoading ? (
        <LoadingState
          compact={directions.length > 0}
          detail={t.loadingDetail}
          label={t.directionLoadingLabel}
          stages={[...t.directionLoadingStages]}
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
                    {direction.matched_evidence[0]?.text ?? t.evidenceSupportedDirection}
                  </span>
                  <span className="direction-meta">
                    <span className={`fit-badge fit-badge--${direction.fit_type}`}>
                      {fitTypeLabels[language][direction.fit_type]}
                    </span>
                    {confidenceLabels[language][direction.confidence_level]} {t.confidenceSuffix}
                  </span>
                </span>
                <span className="score-ring" style={{ "--score": direction.score_midpoint } as CSSProperties}>
                  <strong>{direction.score_midpoint}</strong>
                  <small>{t.fitLabel}</small>
                </span>
              </button>
            );
          })}
        </div>

        {selected ? (
          <aside className="selected-direction-panel">
            <div className="selected-direction-topline">
              <span className={`fit-badge fit-badge--${selected.fit_type}`}>
                {fitTypeLabels[language][selected.fit_type]}
              </span>
              <span>{confidenceLabels[language][selected.confidence_level]} {t.confidenceSuffix}</span>
            </div>
            <h3>{selected.direction}</h3>
            <p>
              {selected.role_family} · {selected.seniority_level} · {selected.score_range_low}
              -{selected.score_range_high} {t.fitRange}
            </p>

            <DirectionSection title={t.whyThisFits}>
              <ul className="clean-list">
                {selected.strengths_for_this_direction.slice(0, 4).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </DirectionSection>

            <DirectionSection title={t.readinessGaps}>
              {selected.gaps_for_this_direction.length ? (
                <ul className="clean-list clean-list--warning">
                  {selected.gaps_for_this_direction.slice(0, 4).map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="empty-copy">{t.noMaterialGaps}</p>
              )}
            </DirectionSection>

            {selected.example_job_titles.length ? (
              <DirectionSection title={t.exampleTitles}>
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
