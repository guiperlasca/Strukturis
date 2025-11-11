import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { PageResult } from "@/types/document";
import { Sparkles, Save, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

interface SplitViewProps {
  page: PageResult;
  onTextChange: (text: string) => void;
  onSave: () => void;
  originalImage?: string;
}

export const SplitView = ({ page, onTextChange, onSave, originalImage }: SplitViewProps) => {
  const [isCorrectingAI, setIsCorrectingAI] = useState(false);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return "text-success";
    if (confidence >= 70) return "text-primary";
    return "text-destructive";
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 90) return "Excelente";
    if (confidence >= 70) return "Boa";
    return "Necessita Revisão";
  };

  const handleCorrectWithAI = async () => {
    setIsCorrectingAI(true);
    try {
      const { data, error } = await supabase.functions.invoke("ai-text-correction", {
        body: { 
          text: page.text,
          context: `Página ${page.pageNumber} de documento`
        },
      });

      if (error) throw error;

      if (data.error) {
        toast.error(data.error);
        return;
      }

      onTextChange(data.corrected);
      toast.success("Texto corrigido com IA!");
    } catch (error) {
      console.error("Error correcting text:", error);
      toast.error("Erro ao corrigir texto");
    } finally {
      setIsCorrectingAI(false);
    }
  };

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Header with confidence */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-2xl font-bold text-foreground">
              Página {page.pageNumber}
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Confiabilidade:</span>
              <span className={cn("text-lg font-bold", getConfidenceColor(page.confidence))}>
                {page.confidence}%
              </span>
              <Badge
                variant={page.confidence >= 90 ? "default" : page.confidence >= 70 ? "secondary" : "destructive"}
              >
                {getConfidenceLabel(page.confidence)}
              </Badge>
            </div>
          </div>

          {page.hasTable && (
            <Badge variant="secondary" className="bg-primary/10 text-primary">
              📊 Tabela Detectada
            </Badge>
          )}
        </div>

        <div className="flex gap-2">
          <Button
            onClick={handleCorrectWithAI}
            disabled={isCorrectingAI}
            className="gap-2"
            variant="outline"
          >
            <Sparkles className="h-4 w-4" />
            {isCorrectingAI ? "Corrigindo..." : "Corrigir trecho com IA"}
          </Button>
          <Button onClick={onSave} className="gap-2 bg-gradient-primary">
            <Save className="h-4 w-4" />
            Salvar
          </Button>
        </div>
      </div>

      {page.confidence < 80 && (
        <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm">
          <AlertCircle className="h-5 w-5 flex-shrink-0 text-destructive" />
          <p className="text-foreground">
            Esta página tem baixa confiabilidade. Recomendamos revisar o texto ou usar a correção com IA.
          </p>
        </div>
      )}

      {/* Split view */}
      <div className="grid flex-1 gap-4 md:grid-cols-2">
        {/* Original Document */}
        <Card className="flex flex-col overflow-hidden">
          <div className="border-b border-border bg-muted px-4 py-3">
            <h3 className="font-semibold text-foreground">Documento Original</h3>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {originalImage ? (
              <img
                src={originalImage}
                alt={`Página ${page.pageNumber}`}
                className="h-auto w-full rounded border border-border"
              />
            ) : (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                <p>Visualização não disponível</p>
              </div>
            )}
          </div>
        </Card>

        {/* OCR Text */}
        <Card className="flex flex-col overflow-hidden">
          <div className="border-b border-border bg-muted px-4 py-3">
            <h3 className="font-semibold text-foreground">Texto Extraído (OCR)</h3>
          </div>
          <div className="flex-1 overflow-auto p-4">
            <Textarea
              value={page.text}
              onChange={(e) => onTextChange(e.target.value)}
              className="min-h-full w-full resize-none border-0 font-mono text-sm focus-visible:ring-0"
              placeholder="Texto extraído aparecerá aqui..."
            />
          </div>
        </Card>
      </div>

      {/* Table preview if detected */}
      {page.hasTable && page.tableData && page.tableData.length > 0 && (
        <Card className="p-4">
          <h3 className="mb-3 font-semibold text-foreground">
            Tabela Detectada
          </h3>
          <div className="overflow-x-auto rounded border border-border">
            <table className="w-full">
              <thead>
                <tr className="bg-muted">
                  {page.tableData[0].map((header, idx) => (
                    <th
                      key={idx}
                      className="border-r border-border px-4 py-2 text-left text-sm font-semibold last:border-r-0"
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {page.tableData.slice(1).map((row, rowIdx) => (
                  <tr key={rowIdx} className="border-t border-border">
                    {row.map((cell, cellIdx) => (
                      <td
                        key={cellIdx}
                        className="border-r border-border px-4 py-2 text-sm last:border-r-0"
                      >
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};
