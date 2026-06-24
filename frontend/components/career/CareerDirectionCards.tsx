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
  showSelectedReport?: boolean;
};

export function CareerDirectionCards({
  directions,
  selected,
  onSelect,
  isLoading = false,
  error = null,
  language = "en",
  showSelectedReport = true,
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

      </div>

      {selected && showSelectedReport ? (
        <SelectedDirectionReport direction={selected} language={language} />
      ) : null}
    </section>
  );
}

export function SelectedDirectionReport({
  direction,
  language = "en",
}: {
  direction: CareerDirection;
  language?: PreferredLanguage;
}) {
  const t = uiCopy[language];
  return (
    <section className="selected-direction-analysis">
      <div className="selected-direction-analysis__header">
        <div>
          <span className="eyebrow">{t.advisorReport}</span>
          <h3>{direction.direction}</h3>
          <p>{t.selectedDirectionSubtitle}</p>
        </div>
        <div className="selected-direction-analysis__meta">
          <span className={`fit-badge fit-badge--${direction.fit_type}`}>
            {fitTypeLabels[language][direction.fit_type]}
          </span>
          <span>{direction.role_family}</span>
          <span>{direction.seniority_level}</span>
          <span>{confidenceLabels[language][direction.confidence_level]} {t.confidenceSuffix}</span>
        </div>
      </div>

      <div className="advisor-report-lead">
        <div>
          <span>{t.recommendationLogic}</span>
          <p>
            {direction.strengths_for_this_direction[0] ??
              direction.matched_evidence[0]?.text ??
              t.evidenceSupportedDirection}
          </p>
        </div>
        {direction.example_job_titles.length ? (
          <div>
            <span>{t.roleTargets}</span>
            <div className="tag-list">
              {direction.example_job_titles.slice(0, 4).map((title) => (
                <span className="tag tag--neutral" key={title}>{title}</span>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      <div className="career-analysis-grid">
        <DirectionSection title={t.keySupportingEvidence}>
          <p className="empty-copy">{t.evidenceAuditBody}</p>
          <div className="evidence-audit-list evidence-audit-list--advisor">
            {direction.matched_evidence.slice(0, 6).map((item, index) => (
              <article className="evidence-audit-item evidence-audit-item--advisor" key={item.evidence_id}>
                <div className="evidence-audit-index">
                  <span>{index + 1}</span>
                  <small>{item.source_type}</small>
                </div>
                <div>
                  <p>{item.text}</p>
                  {item.matched_concepts.length ? (
                    <div className="mini-tag-list">
                      {item.matched_concepts.slice(0, 4).map((concept) => (
                        <span key={concept}>{concept}</span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        </DirectionSection>

        <DirectionSection title={t.whyThisFits}>
          <ul className="advisor-proof-list">
            {direction.strengths_for_this_direction.slice(0, 5).map((item) => (
              <li key={item}>
                <span aria-hidden="true">✓</span>
                <p>{item}</p>
              </li>
            ))}
          </ul>
        </DirectionSection>

        <DirectionSection title={t.rolePositioning}>
          <p className="empty-copy">{t.rolePositioningBody}</p>
          {direction.resume_positioning_advice.length ? (
            <ul className="advisor-proof-list">
              {direction.resume_positioning_advice.slice(0, 4).map((item) => (
                <li key={item}>
                  <span aria-hidden="true">→</span>
                  <p>{item}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-copy">{t.noPositioningAdvice}</p>
          )}
        </DirectionSection>

        <DirectionSection title={t.strengthsAlreadyDemonstrated}>
          <p className="empty-copy">{t.existingEvidenceBody}</p>
          <div className="strength-signal-list">
            {direction.matched_evidence.slice(0, 5).map((item) => (
              <span className="tag tag--neutral" key={item.evidence_id}>
                {item.source_type}
              </span>
            ))}
          </div>
        </DirectionSection>

        <DirectionSection title={t.readinessGaps}>
          {direction.gaps_for_this_direction.length ? (
            <div className="actionable-gap-list">
              {direction.gaps_for_this_direction.slice(0, 5).map((item, index) => (
                <article className="actionable-gap" key={item}>
                  <span>{index + 1}</span>
                  <div>
                    <strong>{t.buildEvidence}</strong>
                    <p>{item}</p>
                    <small>{t.gapActionHint}</small>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-copy">{t.noMaterialGaps}</p>
          )}
        </DirectionSection>

        <DirectionSection title={t.growthRoadmap}>
          <p className="empty-copy">{t.growthRoadmapBody}</p>
          <div className="growth-roadmap-list">
            <article className="growth-roadmap-item">
              <span>1</span>
              <p>{t.roadmapStepEvidence}</p>
            </article>
            <article className="growth-roadmap-item">
              <span>2</span>
              <p>{t.roadmapStepProof}</p>
            </article>
            <article className="growth-roadmap-item">
              <span>3</span>
              <p>{t.roadmapStepResume}</p>
            </article>
          </div>
        </DirectionSection>
      </div>

      {direction.example_job_titles.length ? (
        <DirectionSection title={t.exampleTitles}>
          <div className="tag-list">
            {direction.example_job_titles.slice(0, 7).map((title) => (
              <span className="tag tag--neutral" key={title}>{title}</span>
            ))}
          </div>
        </DirectionSection>
      ) : null}
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
