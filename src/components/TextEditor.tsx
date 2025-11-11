import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageResult } from "@/types/document";
import { Save, AlertCircle, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { AISuggestions } from "./AISuggestions";

interface TextEditorProps {
  pages: PageResult[];
  onSave: (pages: PageResult[]) => void;
}

export const TextEditor = ({ pages, onSave }: TextEditorProps) => {
  const [editedPages, setEditedPages] = useState<PageResult[]>(pages);
  const [hasChanges, setHasChanges] = useState(false);
  const [selectedPageIndex, setSelectedPageIndex] = useState(0);

  const handleTextChange = (pageIndex: number, newText: string) => {
    const updated = [...editedPages];
    updated[pageIndex] = { ...updated[pageIndex], text: newText };
    setEditedPages(updated);
    setHasChanges(true);
  };

  const handleApplyAICorrection = (correctedText: string) => {
    handleTextChange(selectedPageIndex, correctedText);
    toast.success("Correção aplicada com sucesso!");
  };

  const handleSave = () => {
    onSave(editedPages);
    setHasChanges(false);
    toast.success("Alterações salvas com sucesso!");
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return "text-success";
    if (confidence >= 70) return "text-primary";
    return "text-destructive";
  };

  const getConfidenceBadgeVariant = (confidence: number) => {
    if (confidence >= 90) return "default";
    if (confidence >= 70) return "secondary";
    return "destructive";
  };

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-foreground">
            Revisão e Edição Manual
          </h3>
          <p className="text-sm text-muted-foreground">
            Corrija o texto extraído conforme necessário
          </p>
        </div>
        <Button
          onClick={handleSave}
          disabled={!hasChanges}
          className="gap-2 bg-gradient-primary"
        >
          <Save className="h-4 w-4" />
          Salvar Alterações
        </Button>
      </div>

      <Tabs defaultValue="page-1" className="w-full" onValueChange={(value) => {
        const pageNum = parseInt(value.replace("page-", ""));
        setSelectedPageIndex(pageNum - 1);
      }}>
        <TabsList className="mb-4 w-full justify-start overflow-x-auto">
          {editedPages.map((page) => (
            <TabsTrigger
              key={page.pageNumber}
              value={`page-${page.pageNumber}`}
              className="gap-2"
            >
              Página {page.pageNumber}
              <Badge
                variant={getConfidenceBadgeVariant(page.confidence)}
                className="ml-1"
              >
                {page.confidence}%
              </Badge>
            </TabsTrigger>
          ))}
        </TabsList>

        {editedPages.map((page, index) => (
          <TabsContent key={page.pageNumber} value={`page-${page.pageNumber}`}>
            <div className="space-y-4">
              {/* AI Suggestions */}
              {page.confidence < 90 && (
                <AISuggestions
                  text={page.text}
                  context={`Página ${page.pageNumber} de documento`}
                  onApply={handleApplyAICorrection}
                />
              )}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground">
                    Confiabilidade da Página:
                  </span>
                  <span className={cn("text-lg font-bold", getConfidenceColor(page.confidence))}>
                    {page.confidence}%
                  </span>
                </div>

                {page.confidence < 80 && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <AlertCircle className="h-4 w-4 text-destructive" />
                    Revisão recomendada
                  </div>
                )}

                {page.hasTable && (
                  <Badge variant="secondary" className="bg-primary/10 text-primary">
                    Tabela Detectada
                  </Badge>
                )}
              </div>

              <Textarea
                value={page.text}
                onChange={(e) => handleTextChange(index, e.target.value)}
                className="min-h-[400px] font-mono text-sm"
                placeholder="Texto extraído aparecerá aqui..."
              />

              {page.hasTable && page.tableData && (
                <div className="rounded-lg bg-muted p-4">
                  <p className="mb-2 text-sm font-medium text-foreground">
                    Dados da Tabela:
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-sm">
                      <tbody>
                        {page.tableData.map((row, rowIndex) => (
                          <tr key={rowIndex} className="border-b border-border">
                            {row.map((cell, cellIndex) => (
                              <td
                                key={cellIndex}
                                className="border-r border-border p-2 last:border-r-0"
                              >
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </Card>
  );
};
