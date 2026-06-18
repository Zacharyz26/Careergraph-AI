type ErrorMessageProps = {
  message: string;
  onDismiss?: () => void;
  title?: string;
  dismissLabel?: string;
};

export function ErrorMessage({
  message,
  onDismiss,
  title = "Something needs attention",
  dismissLabel = "Dismiss error",
}: ErrorMessageProps) {
  return (
    <div className="error-message" role="alert">
      <span className="error-icon" aria-hidden="true">
        !
      </span>
      <div>
        <strong>{title}</strong>
        <p>{message}</p>
      </div>
      {onDismiss ? (
        <button className="icon-button" onClick={onDismiss} type="button">
          <span className="sr-only">{dismissLabel}</span>
          ×
        </button>
      ) : null}
    </div>
  );
}
