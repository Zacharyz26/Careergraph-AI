type ErrorMessageProps = {
  message: string;
  onDismiss?: () => void;
};

export function ErrorMessage({ message, onDismiss }: ErrorMessageProps) {
  return (
    <div className="error-message" role="alert">
      <span className="error-icon" aria-hidden="true">
        !
      </span>
      <div>
        <strong>Something needs attention</strong>
        <p>{message}</p>
      </div>
      {onDismiss ? (
        <button className="icon-button" onClick={onDismiss} type="button">
          <span className="sr-only">Dismiss error</span>
          ×
        </button>
      ) : null}
    </div>
  );
}
