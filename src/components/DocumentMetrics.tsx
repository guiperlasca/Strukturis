import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { FileText, Table, AlertTriangle, CheckCircle2 } from "lucide-react";
import { ProcessedDocument } from "@/types/document";

interface DocumentMetricsProps {
  document: ProcessedDocument;
}

export const DocumentMetrics = ({ document }: DocumentMetricsProps) => {
  const { summary, pages } = document;

  if (!summary) return null;

  const criticalPages = pages.filter(p => p.status !== 'ok');
  const hasIssues = criticalPages.length > 0;

  return (
    <div className="space-y-6">
      {/* Metrics Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Confiabilidade</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.readabilityConfidence}%</div>
            <Progress value={summary.readabilityConfidence} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Taxa de Sucesso</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.pageSuccessRate}%</div>
            <Progress value={summary.pageSuccessRate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tabelas</CardTitle>
            <Table className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.tablesDetected}</div>
            <p className="text-xs text-muted-foreground mt-2">
              detectadas no documento
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Campos</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary.fieldsDetected}</div>
            <p className="text-xs text-muted-foreground mt-2">
              campos extraídos
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Critical Pages Report */}
      {hasIssues && (
        <Card className="border-destructive/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Relatório de Páginas Críticas
            </CardTitle>
            <CardDescription>
              {criticalPages.length} página(s) com problemas de qualidade
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {criticalPages.map((page) => (
                <div
                  key={page.pageNumber}
                  className="flex items-start gap-4 rounded-lg border border-border p-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold">Página {page.pageNumber}</span>
                      <Badge variant={page.status === 'error' ? 'destructive' : 'secondary'}>
                        {page.status === 'error' ? 'Erro' : 'Baixa Qualidade'}
                      </Badge>
                    </div>
                    {page.qualityHints && page.qualityHints.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {page.qualityHints.map((hint, idx) => (
                          <Badge key={idx} variant="outline">
                            {hint === 'skew' && 'Inclinação'}
                            {hint === 'blur' && 'Desfocado'}
                            {hint === 'shadow' && 'Sombra'}
                            {hint !== 'skew' && hint !== 'blur' && hint !== 'shadow' && hint}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Export Options */}
      {document.exports && (
        <Card>
          <CardHeader>
            <CardTitle>Downloads</CardTitle>
            <CardDescription>Baixe os dados processados</CardDescription>
          </CardHeader>
          <CardContent className="flex gap-4">
            {document.exports.jsonUrl && (
              <a
                href={document.exports.jsonUrl}
                download
                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
              >
                <FileText className="mr-2 h-4 w-4" />
                Baixar JSON
              </a>
            )}
            {document.exports.csvUrl && (
              <a
                href={document.exports.csvUrl}
                download
                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
              >
                <Table className="mr-2 h-4 w-4" />
                Baixar CSV (Tabelas)
              </a>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};
