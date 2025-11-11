import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Card } from "@/components/ui/card";
import { AlertCircle, FileText } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface PageSelectorProps {
  totalPages: number;
  onConfirm: (selectedPages: number[]) => void;
  onCancel: () => void;
}

export const PageSelector = ({ totalPages, onConfirm, onCancel }: PageSelectorProps) => {
  const [selectionMode, setSelectionMode] = useState<"all" | "first-n" | "manual">("all");
  const [firstNPages, setFirstNPages] = useState("10");
  const [manualSelection, setManualSelection] = useState("");
  const [error, setError] = useState("");
  const [selectedPages, setSelectedPages] = useState<number[]>([]);

  const parseManualSelection = (input: string): number[] => {
    const pages = new Set<number>();
    const parts = input.split(",").map(p => p.trim());

    for (const part of parts) {
      if (part.includes("-")) {
        const [start, end] = part.split("-").map(n => parseInt(n.trim()));
        if (isNaN(start) || isNaN(end) || start < 1 || end > totalPages || start > end) {
          throw new Error(`Intervalo inválido: ${part}`);
        }
        for (let i = start; i <= end; i++) {
          pages.add(i);
        }
      } else {
        const pageNum = parseInt(part);
        if (isNaN(pageNum) || pageNum < 1 || pageNum > totalPages) {
          throw new Error(`Página inválida: ${part}`);
        }
        pages.add(pageNum);
      }
    }

    return Array.from(pages).sort((a, b) => a - b);
  };

  const handlePreview = () => {
    setError("");
    try {
      let pages: number[] = [];

      if (selectionMode === "all") {
        pages = Array.from({ length: totalPages }, (_, i) => i + 1);
      } else if (selectionMode === "first-n") {
        const n = parseInt(firstNPages);
        if (isNaN(n) || n < 1 || n > totalPages) {
          throw new Error(`Número de páginas inválido. Deve ser entre 1 e ${totalPages}`);
        }
        pages = Array.from({ length: n }, (_, i) => i + 1);
      } else {
        if (!manualSelection.trim()) {
          throw new Error("Digite as páginas que deseja processar");
        }
        pages = parseManualSelection(manualSelection);
      }

      setSelectedPages(pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao processar seleção");
      setSelectedPages([]);
    }
  };

  const handleConfirm = () => {
    if (selectedPages.length === 0) {
      setError("Selecione as páginas antes de confirmar");
      return;
    }
    onConfirm(selectedPages);
  };

  return (
    <Card className="mx-auto max-w-2xl p-6">
      <div className="mb-6 flex items-center gap-3">
        <FileText className="h-6 w-6 text-primary" />
        <div>
          <h2 className="text-xl font-semibold text-foreground">
            Modo Seguro de Processamento
          </h2>
          <p className="text-sm text-muted-foreground">
            Total de páginas detectadas: <span className="font-medium">{totalPages}</span>
          </p>
        </div>
      </div>

      <RadioGroup value={selectionMode} onValueChange={(v: any) => setSelectionMode(v)}>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="all" id="all" />
            <Label htmlFor="all" className="cursor-pointer">
              Processar todas as páginas ({totalPages} páginas)
            </Label>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="first-n" id="first-n" />
              <Label htmlFor="first-n" className="cursor-pointer">
                Processar apenas as primeiras N páginas
              </Label>
            </div>
            {selectionMode === "first-n" && (
              <Input
                type="number"
                min="1"
                max={totalPages}
                value={firstNPages}
                onChange={(e) => setFirstNPages(e.target.value)}
                placeholder={`Máximo: ${totalPages}`}
                className="ml-6 max-w-xs"
              />
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="manual" id="manual" />
              <Label htmlFor="manual" className="cursor-pointer">
                Selecionar páginas manualmente
              </Label>
            </div>
            {selectionMode === "manual" && (
              <div className="ml-6 space-y-2">
                <Input
                  value={manualSelection}
                  onChange={(e) => setManualSelection(e.target.value)}
                  placeholder='Ex: "3" ou "3-5" ou "1,4,6"'
                  className="max-w-xs"
                />
                <p className="text-xs text-muted-foreground">
                  Use vírgulas para páginas individuais e hífen para intervalos
                </p>
              </div>
            )}
          </div>
        </div>
      </RadioGroup>

      {error && (
        <Alert variant="destructive" className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {selectedPages.length > 0 && (
        <div className="mt-6 rounded-lg bg-secondary p-4">
          <h3 className="mb-2 font-medium text-secondary-foreground">
            Resumo da Seleção
          </h3>
          <p className="mb-2 text-sm text-muted-foreground">
            Você selecionou processar as páginas:
          </p>
          <p className="font-mono text-sm text-foreground">
            {selectedPages.length <= 10
              ? selectedPages.join(", ")
              : `${selectedPages.slice(0, 10).join(", ")}... (+${selectedPages.length - 10} páginas)`}
          </p>
          <p className="mt-2 text-sm font-medium text-secondary-foreground">
            Total: {selectedPages.length} página{selectedPages.length !== 1 ? "s" : ""}
          </p>
        </div>
      )}

      <div className="mt-6 flex gap-3">
        <Button onClick={handlePreview} variant="outline" className="flex-1">
          Visualizar Seleção
        </Button>
        <Button onClick={handleConfirm} disabled={selectedPages.length === 0} className="flex-1">
          Confirmar Processamento
        </Button>
        <Button onClick={onCancel} variant="ghost">
          Cancelar
        </Button>
      </div>
    </Card>
  );
};
