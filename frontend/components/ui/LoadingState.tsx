"use client";

import { useEffect, useState } from "react";

type LoadingStateProps = {
  label: string;
  detail?: string;
  compact?: boolean;
  stages?: string[];
  stageIntervalMs?: number;
};

export function LoadingState({
  label,
  detail,
  compact = false,
  stages = [],
  stageIntervalMs = 3500,
}: LoadingStateProps) {
  const [stageIndex, setStageIndex] = useState(0);
  const activeStage = stages[stageIndex] ?? null;

  useEffect(() => {
    if (stages.length <= 1) return;
    const timer = window.setInterval(() => {
      setStageIndex((current) => Math.min(current + 1, stages.length - 1));
    }, stageIntervalMs);
    return () => window.clearInterval(timer);
  }, [stageIntervalMs, stages.length]);

  return (
    <div
      aria-live="polite"
      className={`loading-state${compact ? " loading-state--compact" : ""}`}
      role="status"
    >
      <div className="loading-state__message">
        <span className="analysis-orb" aria-hidden="true">
          <span />
        </span>
        <span>
          <strong>{label}</strong>
          {activeStage ? <small>{activeStage}</small> : null}
          {detail ? <small>{detail}</small> : null}
        </span>
      </div>
      {stages.length > 1 ? (
        <div className="loading-stage-list" aria-hidden="true">
          {stages.map((stage, index) => (
            <span
              className={index <= stageIndex ? "loading-stage loading-stage--active" : "loading-stage"}
              key={stage}
            />
          ))}
        </div>
      ) : null}
      <span className="loading-progress" aria-hidden="true">
        <span />
      </span>
    </div>
  );
}
