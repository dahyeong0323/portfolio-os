import { Check, CircleDot } from "lucide-react";

const steps = ["스냅샷 가져오기", "Artifact 확인", "정산 실행", "차이 검토", "보고서"];

export function ReconciliationStepper({ activeStep }: { activeStep: number }) {
  return (
    <ol className="reconciliation-stepper" aria-label="정산 진행 단계">
      {steps.map((label, index) => {
        const step = index + 1;
        const complete = step < activeStep;
        const active = step === activeStep;
        return (
          <li key={label} className={complete ? "is-complete" : active ? "is-active" : undefined} aria-current={active ? "step" : undefined}>
            <span className="reconciliation-stepper__marker" aria-hidden="true">
              {complete ? <Check /> : active ? <CircleDot /> : step}
            </span>
            <span><small>STEP {step}</small><strong>{label}</strong></span>
          </li>
        );
      })}
    </ol>
  );
}
