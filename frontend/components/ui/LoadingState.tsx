type LoadingStateProps = {
  label: string;
  detail?: string;
  compact?: boolean;
};

export function LoadingState({
  label,
  detail,
  compact = false,
}: LoadingStateProps) {
  return (
    <div
      aria-live="polite"
      className={`loading-state${compact ? " loading-state--compact" : ""}`}
      role="status"
    >
      <div className="loading-state__message">
        <span className="spinner" aria-hidden="true" />
        <span>
          <strong>{label}</strong>
          {detail ? <small>{detail}</small> : null}
        </span>
      </div>
      <span className="loading-progress" aria-hidden="true">
        <span />
      </span>
    </div>
  );
}
