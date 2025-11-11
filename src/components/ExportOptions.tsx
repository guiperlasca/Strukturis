import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FileText, FileSpreadsheet, FileJson, FileCode, Download } from "lucide-react";
import { ProcessedDocument } from "@/types/document";
import {
  exportToTxt,
  exportToCsv,
  exportToJson,
  exportToHtml,
  downloadBlob,
} from "@/utils/exporters";
import { toast } from "sonner";

interface ExportOptionsProps {
  document: ProcessedDocument;
}

const exportOptions = [
  {
    id: "txt",
    label: "Texto (.txt)",
    icon: FileText,
    description: "Arquivo de texto simples",
  },
  {
    id: "html",
    label: "HTML",
    icon: FileCode,
    description: "Documento HTML formatado",
  },
  {
    id: "csv",
    label: "Tabelas (.csv)",
    icon: FileSpreadsheet,
    description: "Tabelas em formato CSV",
  },
  {
    id: "json",
    label: "JSON API",
    icon: FileJson,
    description: "Formato JSON para integração",
  },
];

export const ExportOptions = ({ document }: ExportOptionsProps) => {
  const handleExport = (format: string) => {
    try {
      let blob: Blob;
      let fileName: string;

      const baseName = document.originalFile.name.replace(/\.[^/.]+$/, "");

      switch (format) {
        case "txt":
          blob = exportToTxt(document);
          fileName = `${baseName}-strukturis.txt`;
          break;
        case "html":
          blob = exportToHtml(document);
          fileName = `${baseName}-strukturis.html`;
          break;
        case "csv":
          blob = exportToCsv(document);
          fileName = `${baseName}-tabelas.csv`;
          break;
        case "json":
          blob = exportToJson(document);
          fileName = `${baseName}-strukturis.json`;
          break;
        default:
          throw new Error("Formato não suportado");
      }

      downloadBlob(blob, fileName);
      toast.success(`Arquivo exportado: ${fileName}`);
    } catch (error) {
      console.error("Erro ao exportar:", error);
      toast.error("Erro ao exportar documento");
    }
  };

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h3 className="mb-2 text-lg font-semibold text-foreground">
          Exportar Documento
        </h3>
        <p className="text-sm text-muted-foreground">
          Escolha o formato desejado para download
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {exportOptions.map((option) => {
          const Icon = option.icon;
          return (
            <Button
              key={option.id}
              onClick={() => handleExport(option.id)}
              variant="outline"
              className="h-auto justify-start gap-4 p-4 text-left transition-all hover:border-primary hover:bg-primary/5"
            >
              <div className="rounded-lg bg-gradient-primary p-3">
                <Icon className="h-5 w-5 text-primary-foreground" />
              </div>
              <div className="flex-1">
                <div className="font-semibold text-foreground">{option.label}</div>
                <div className="text-xs text-muted-foreground">{option.description}</div>
              </div>
              <Download className="h-5 w-5 text-muted-foreground" />
            </Button>
          );
        })}
      </div>

      <div className="mt-6 rounded-lg bg-muted p-4">
        <p className="text-sm text-muted-foreground">
          💡 <strong>Dica:</strong> Arquivos HTML preservam formatação completa.
          Use CSV para importar tabelas no Excel. JSON é ideal para integração via API.
        </p>
      </div>
    </Card>
  );
};
