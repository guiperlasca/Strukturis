import { Loader2 } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface ProcessingStatusProps {
  progress: number;
  status: string;
  currentPage?: number;
  totalPages?: number;
}

export const ProcessingStatus = ({ progress, status, currentPage, totalPages }: ProcessingStatusProps) => {
  return (
    <div className="rounded-2xl border border-border bg-card p-8 shadow-md">
      <div className="mb-6 flex items-center justify-center">
        <div className="rounded-full bg-gradient-primary p-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary-foreground" />
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <p className="mb-2 text-center text-lg font-medium text-foreground">
            {status}
          </p>
          <Progress value={progress} className="h-2" />
        </div>

        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            Processando com OCR avançado e IA...
          </p>
          {currentPage && totalPages && (
            <p className="mt-1 text-xs text-muted-foreground">
              Página {currentPage} de {totalPages}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
