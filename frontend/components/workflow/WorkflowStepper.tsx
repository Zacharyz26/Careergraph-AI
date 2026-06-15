const steps = [
  "Upload",
  "Profile",
  "Directions",
  "Suggestions",
  "Job match",
] as const;

export function WorkflowStepper({ currentStep }: { currentStep: number }) {
  return (
    <ol className="workflow-stepper" aria-label="Workflow progress">
      {steps.map((step, index) => {
        const number = index + 1;
        const state =
          number < currentStep
            ? "complete"
            : number === currentStep
              ? "active"
              : "pending";
        return (
          <li className={`workflow-step workflow-step--${state}`} key={step}>
            <span className="step-number" aria-hidden="true">
              {state === "complete" ? "✓" : number}
            </span>
            <span className="step-label">{step}</span>
          </li>
        );
      })}
    </ol>
  );
}
