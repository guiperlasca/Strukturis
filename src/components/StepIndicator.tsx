import { Check } from "lucide-react";
import { ProcessStep } from "@/types/document";
import { cn } from "@/lib/utils";

interface StepIndicatorProps {
  currentStep: ProcessStep;
  completedSteps: ProcessStep[];
}

const steps: { id: ProcessStep; label: string }[] = [
  { id: "upload", label: "Upload" },
  { id: "preprocessing", label: "Correção de Imagem" },
  { id: "ocr", label: "OCR com IA" },
  { id: "extraction", label: "Extração" },
  { id: "review", label: "Revisão" },
  { id: "export", label: "Exportação" },
];

export const StepIndicator = ({ currentStep, completedSteps }: StepIndicatorProps) => {
  const currentIndex = steps.findIndex((s) => s.id === currentStep);

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = completedSteps.includes(step.id);
          const isCurrent = step.id === currentStep;
          const isUpcoming = index > currentIndex;

          return (
            <div key={step.id} className="flex flex-1 items-center">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-300",
                    isCompleted && "border-success bg-success text-success-foreground",
                    isCurrent && "border-primary bg-primary text-primary-foreground shadow-glow",
                    isUpcoming && "border-border bg-muted text-muted-foreground"
                  )}
                >
                  {isCompleted ? (
                    <Check className="h-5 w-5" />
                  ) : (
                    <span className="text-sm font-semibold">{index + 1}</span>
                  )}
                </div>
                <span
                  className={cn(
                    "mt-2 text-xs font-medium transition-colors",
                    (isCompleted || isCurrent) && "text-foreground",
                    isUpcoming && "text-muted-foreground"
                  )}
                >
                  {step.label}
                </span>
              </div>

              {index < steps.length - 1 && (
                <div
                  className={cn(
                    "mx-2 h-0.5 flex-1 transition-all duration-300",
                    isCompleted ? "bg-success" : "bg-border"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
