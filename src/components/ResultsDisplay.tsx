import { CheckCircle2, Download, Copy, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

interface ResultsDisplayProps {
  text: string;
  confidence: number;
  pages?: number;
  onReset: () => void;
}

export const ResultsDisplay = ({ text, confidence, pages, onReset }: ResultsDisplayProps) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    toast.success("Texto copiado para a área de transferência!");
  };

  const handleDownload = () => {
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "strukturis-texto-extraido.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Arquivo baixado com sucesso!");
  };

  const getConfidenceColor = () => {
    if (confidence >= 90) return "bg-gradient-success";
    if (confidence >= 70) return "bg-gradient-primary";
    return "bg-destructive";
  };

  const getConfidenceLabel = () => {
    if (confidence >= 90) return "Excelente";
    if (confidence >= 70) return "Boa";
    return "Regular";
  };

  return (
    <div className="space-y-6">
      <Card className="p-6 shadow-lg">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-gradient-success p-2">
              <CheckCircle2 className="h-6 w-6 text-success-foreground" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">
                Extração Concluída
              </h3>
              <p className="text-sm text-muted-foreground">
                {pages ? `${pages} página${pages > 1 ? 's' : ''} processada${pages > 1 ? 's' : ''}` : 'Texto processado com sucesso'}
              </p>
            </div>
          </div>

          <Badge className={`${getConfidenceColor()} px-4 py-2 text-white`}>
            <span className="font-semibold">{confidence}%</span>
            <span className="ml-2 text-xs">{getConfidenceLabel()}</span>
          </Badge>
        </div>

        <div className="mb-4 rounded-lg bg-secondary p-4">
          <p className="whitespace-pre-wrap break-words text-sm text-secondary-foreground">
            {text || "Nenhum texto extraído."}
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button onClick={handleCopy} variant="outline" className="gap-2">
            <Copy className="h-4 w-4" />
            Copiar Texto
          </Button>
          <Button onClick={handleDownload} className="gap-2 bg-gradient-primary">
            <Download className="h-4 w-4" />
            Baixar TXT
          </Button>
          <Button onClick={onReset} variant="secondary" className="gap-2">
            <RotateCcw className="h-4 w-4" />
            Processar Novo
          </Button>
        </div>
      </Card>

      <Card className="bg-secondary/50 p-4">
        <div className="flex items-start gap-3">
          <div className="rounded bg-primary/10 p-2">
            <CheckCircle2 className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <h4 className="mb-1 font-medium text-foreground">
              Taxa de Confiabilidade
            </h4>
            <p className="text-sm text-muted-foreground">
              A taxa de {confidence}% indica a precisão estimada da extração. 
              Valores acima de 90% representam alta confiabilidade.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
