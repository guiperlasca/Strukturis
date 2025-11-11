import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Check, Loader2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

interface AISuggestionsProps {
  text: string;
  context?: string;
  onApply: (correctedText: string) => void;
}

export const AISuggestions = ({ text, context, onApply }: AISuggestionsProps) => {
  const [isLoading, setIsLoading] = useState(false);
  const [correction, setCorrection] = useState<string | null>(null);

  const handleCorrectWithAI = async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke("ai-text-correction", {
        body: { text, context },
      });

      if (error) throw error;

      if (data.error) {
        if (data.error.includes("Rate limit")) {
          toast.error("Limite de requisições atingido. Tente novamente em alguns instantes.");
        } else if (data.error.includes("credits")) {
          toast.error("Créditos de IA esgotados. Adicione créditos para continuar.");
        } else {
          toast.error(data.error);
        }
        return;
      }

      setCorrection(data.corrected);
      toast.success("Texto corrigido pela IA!");
    } catch (error) {
      console.error("Error correcting text:", error);
      toast.error("Erro ao corrigir texto com IA");
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyCorrection = () => {
    if (correction) {
      onApply(correction);
      setCorrection(null);
      toast.success("Correção aplicada!");
    }
  };

  if (!text || text.length < 10) return null;

  return (
    <Card className="border-primary/20 bg-primary/5 p-4">
      <div className="flex items-start gap-3">
        <div className="rounded-lg bg-gradient-primary p-2">
          <Sparkles className="h-5 w-5 text-primary-foreground" />
        </div>
        <div className="flex-1">
          <div className="mb-2 flex items-center gap-2">
            <h4 className="font-semibold text-foreground">Correção com IA</h4>
            <Badge variant="secondary" className="text-xs">
              Suporte por IA
            </Badge>
          </div>
          <p className="mb-3 text-sm text-muted-foreground">
            Use inteligência artificial para corrigir automaticamente erros de OCR baseando-se no contexto do documento.
          </p>

          {correction && (
            <div className="mb-3 rounded-lg bg-card p-3">
              <p className="mb-1 text-xs font-medium text-muted-foreground">
                Texto corrigido:
              </p>
              <p className="whitespace-pre-wrap text-sm text-foreground">
                {correction}
              </p>
            </div>
          )}

          <div className="flex gap-2">
            {!correction ? (
              <Button
                onClick={handleCorrectWithAI}
                disabled={isLoading}
                className="gap-2 bg-gradient-primary"
                size="sm"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Corrigindo...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Corrigir com IA
                  </>
                )}
              </Button>
            ) : (
              <>
                <Button
                  onClick={handleApplyCorrection}
                  className="gap-2 bg-gradient-success"
                  size="sm"
                >
                  <Check className="h-4 w-4" />
                  Aplicar Correção
                </Button>
                <Button
                  onClick={() => setCorrection(null)}
                  variant="outline"
                  size="sm"
                >
                  Cancelar
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};
