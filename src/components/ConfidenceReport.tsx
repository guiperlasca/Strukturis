import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { ProcessedDocument } from "@/types/document";
import { 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  FileText,
  TrendingUp,
  Calendar,
  Languages
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ConfidenceReportProps {
  document: ProcessedDocument;
}

export const ConfidenceReport = ({ document }: ConfidenceReportProps) => {
  const getConfidenceLevel = (confidence: number): "high" | "medium" | "low" => {
    if (confidence >= 90) return "high";
    if (confidence >= 70) return "medium";
    return "low";
  };

  const getConfidenceIcon = (level: "high" | "medium" | "low") => {
    switch (level) {
      case "high":
        return <CheckCircle2 className="h-5 w-5 text-success" />;
      case "medium":
        return <AlertTriangle className="h-5 w-5 text-primary" />;
      case "low":
        return <XCircle className="h-5 w-5 text-destructive" />;
    }
  };

  const getConfidenceColor = (level: "high" | "medium" | "low") => {
    switch (level) {
      case "high":
        return "text-success";
      case "medium":
        return "text-primary";
      case "low":
        return "text-destructive";
    }
  };

  const overallLevel = getConfidenceLevel(document.overallConfidence);
  
  const pageStats = {
    high: document.pages.filter((p) => p.confidence >= 90).length,
    medium: document.pages.filter((p) => p.confidence >= 70 && p.confidence < 90).length,
    low: document.pages.filter((p) => p.confidence < 70).length,
  };

  const tablesDetected = document.pages.filter((p) => p.hasTable).length;

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="mb-2 text-xl font-bold text-foreground">
          Relatório de Confiabilidade
        </h3>
        <p className="text-sm text-muted-foreground">
          Análise detalhada da qualidade da extração OCR
        </p>
      </div>

      {/* Overall Confidence */}
      <div className="mb-6 rounded-lg bg-gradient-primary p-6 text-primary-foreground">
        <div className="flex items-center justify-between">
          <div>
            <p className="mb-1 text-sm opacity-90">Confiabilidade Geral</p>
            <div className="flex items-center gap-3">
              <span className="text-5xl font-bold">{document.overallConfidence}%</span>
              <div className="flex flex-col gap-1">
                {getConfidenceIcon(overallLevel)}
                <span className="text-xs font-medium">
                  {overallLevel === "high" && "Excelente"}
                  {overallLevel === "medium" && "Boa"}
                  {overallLevel === "low" && "Regular"}
                </span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm opacity-90">Total de Páginas</p>
            <p className="text-3xl font-bold">{document.totalPages}</p>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <Card className="bg-secondary/50 p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gradient-primary p-2">
              <FileText className="h-5 w-5 text-primary-foreground" />
            </div>
          <div>
            <p className="text-xs text-muted-foreground">Tipo de Documento</p>
            <p className="font-semibold text-foreground">
              {document.documentType?.label || "Detectando..."}
            </p>
          </div>
          </div>
        </Card>

        <Card className="bg-secondary/50 p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-gradient-success p-2">
              <TrendingUp className="h-5 w-5 text-success-foreground" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Tabelas Detectadas</p>
              <p className="font-semibold text-foreground">{tablesDetected}</p>
            </div>
          </div>
        </Card>

        <Card className="bg-secondary/50 p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary p-2">
              <Languages className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Idioma Detectado</p>
              <p className="font-semibold text-foreground">
                {document.detectedLanguage === "pt-BR" && "Português"}
                {document.detectedLanguage === "en" && "Inglês"}
                {document.detectedLanguage === "es" && "Espanhol"}
                {!document.detectedLanguage && "Português"}
              </p>
            </div>
          </div>
        </Card>

        <Card className="bg-secondary/50 p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-accent p-2">
              <Calendar className="h-5 w-5 text-accent-foreground" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Processado em</p>
              <p className="text-xs font-semibold text-foreground">
                {document.processedAt.toLocaleString("pt-BR")}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Page Statistics */}
      <div className="mb-6">
        <h4 className="mb-3 font-semibold text-foreground">
          Distribuição de Confiabilidade
        </h4>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="flex items-center gap-3 rounded-lg border border-border bg-card p-3">
            <CheckCircle2 className="h-6 w-6 text-success" />
            <div className="flex-1">
              <p className="text-sm text-muted-foreground">Alta (≥90%)</p>
              <p className="text-xl font-bold text-foreground">{pageStats.high}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-lg border border-border bg-card p-3">
            <AlertTriangle className="h-6 w-6 text-primary" />
            <div className="flex-1">
              <p className="text-sm text-muted-foreground">Média (70-89%)</p>
              <p className="text-xl font-bold text-foreground">{pageStats.medium}</p>
            </div>
          </div>

          <div className="flex items-center gap-3 rounded-lg border border-border bg-card p-3">
            <XCircle className="h-6 w-6 text-destructive" />
            <div className="flex-1">
              <p className="text-sm text-muted-foreground">Baixa (&lt;70%)</p>
              <p className="text-xl font-bold text-foreground">{pageStats.low}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Per-Page Confidence */}
      <div>
        <h4 className="mb-3 font-semibold text-foreground">
          Confiabilidade por Página
        </h4>
        <div className="space-y-3">
          {document.pages.map((page) => {
            const level = getConfidenceLevel(page.confidence);
            return (
              <div key={page.pageNumber} className="flex items-center gap-3">
                <div className="flex w-32 items-center gap-2">
                  <span className="text-sm font-medium text-foreground">
                    Página {page.pageNumber}
                  </span>
                  {page.hasTable && (
                    <Badge variant="secondary" className="text-xs">
                      Tabela
                    </Badge>
                  )}
                </div>
                <div className="flex-1">
                  <Progress 
                    value={page.confidence} 
                    className={cn(
                      "h-2",
                      level === "high" && "[&>div]:bg-success",
                      level === "medium" && "[&>div]:bg-primary",
                      level === "low" && "[&>div]:bg-destructive"
                    )}
                  />
                </div>
                <div className="flex w-20 items-center justify-end gap-2">
                  <span className={cn("text-sm font-bold", getConfidenceColor(level))}>
                    {page.confidence}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recommendations */}
      {pageStats.low > 0 && (
        <div className="mt-6 rounded-lg bg-destructive/10 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 flex-shrink-0 text-destructive" />
            <div>
              <p className="font-semibold text-foreground">Recomendação</p>
              <p className="text-sm text-muted-foreground">
                {pageStats.low} página{pageStats.low > 1 ? "s" : ""} com baixa confiabilidade.
                Recomendamos revisão manual dessas páginas antes da exportação final.
              </p>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};
