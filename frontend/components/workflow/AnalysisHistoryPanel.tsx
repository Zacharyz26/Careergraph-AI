"use client";

import { formatCopy, type PreferredLanguage, uiCopy } from "@/lib/i18n";
import type { AnalysisHistoryItem } from "@/lib/types";

type AnalysisHistoryPanelProps = {
  analyses: AnalysisHistoryItem[];
  isLoading: boolean;
  language: PreferredLanguage;
  onOpen: (analysisId: string) => void;
};

export function AnalysisHistoryPanel({
  analyses,
  isLoading,
  language,
  onOpen,
}: AnalysisHistoryPanelProps) {
  const t = uiCopy[language];
  return (
    <section className="analysis-history-panel">
      <div className="analysis-history-panel__header">
        <div>
          <span className="eyebrow">{t.savedAnalysis}</span>
          <h2>{t.analysisHistoryTitle}</h2>
          <p>{t.analysisHistoryBody}</p>
        </div>
      </div>

      {isLoading ? <p className="inline-note">{t.loadingHistory}</p> : null}
      {!isLoading && analyses.length === 0 ? (
        <p className="inline-note">{t.noAnalysisHistory}</p>
      ) : null}

      {analyses.length ? (
        <div className="analysis-history-list">
          {analyses.map((analysis) => (
            <article className="analysis-history-item" key={analysis.analysis_id}>
              <div>
                <strong>
                  {analysis.candidate_name || analysis.filename || t.savedAnalysis}
                </strong>
                <span>{analysis.top_direction || analysis.status}</span>
                <small>
                  {formatCopy(t.lastUpdated, {
                    date: new Date(analysis.updated_at).toLocaleDateString(),
                  })}
                  {" · "}
                  {formatCopy(t.suggestionsSaved, {
                    count: analysis.suggestion_count.toLocaleString(),
                  })}
                </small>
              </div>
              <button
                className="button button--primary"
                onClick={() => onOpen(analysis.analysis_id)}
                type="button"
              >
                {t.openAnalysis}
              </button>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
