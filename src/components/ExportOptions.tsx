import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FileText, FileSpreadsheet, FileJson, FileCode, Download, FileType } from "lucide-react";
import { ProcessedDocument } from "@/types/document";
import {
  exportToTxt,
  exportToCsv,
  exportToJson,
  exportToHtml,
  exportToExcel,
  exportToWord,
  exportToPDF,
  downloadBlob,
} from "@/utils/exporters";
import { toast } from "sonner";
import { useState } from "react";

interface ExportOptionsProps {
  document: ProcessedDocument;
}

const exportOptions = [
  {
    id: "excel",
    label: "Excel (.xlsx)",
    icon: FileSpreadsheet,
    description: "Planilha com múltiplas abas e tabelas",
    featured: true,
  },
  {
    id: "word",
    label: "Word (.docx)",
    icon: FileType,
    description: "Documento editável do Microsoft Word",
    featured: true,
  },
  {
    id: "pdf",
    label: "PDF Pesquisável",
    icon: FileText,
    description: "PDF com texto pesquisável e formatado",
    featured: true,
  },
  {
    id: "json",
    label: "JSON API",
    icon: FileJson,
    description: "Formato JSON para integração de sistemas",
    featured: true,
  },
  {
    id: "txt",
    label: "Texto (.txt)",
    icon: FileText,
    description: "Arquivo de texto simples",
    featured: false,
  },
  {
    id: "html",
    label: "HTML",
    icon: FileCode,
    description: "Documento HTML formatado",
    featured: false,
  },
  {
    id: "csv",
    label: "Tabelas (.csv)",
    icon: FileSpreadsheet,
    description: "Apenas tabelas em formato CSV",
    featured: false,
  },
];

export const ExportOptions = ({ document }: ExportOptionsProps) => {
  const [exporting, setExporting] = useState<string | null>(null);

  const handleExport = async (format: string) => {
    setExporting(format);
    try {
      let blob: Blob;
      let fileName: string;

      const baseName = document.originalFile.name.replace(/\.[^/.]+$/, "");

      switch (format) {
        case "excel":
          blob = exportToExcel(document);
          fileName = `${baseName}-strukturis.xlsx`;
          break;
        case "word":
          blob = await exportToWord(document);
          fileName = `${baseName}-strukturis.docx`;
          break;
        case "pdf":
          blob = exportToPDF(document);
          fileName = `${baseName}-strukturis.pdf`;
          break;
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
    } finally {
      setExporting(null);
    }
  };

  const featuredOptions = exportOptions.filter((opt) => opt.featured);
  const otherOptions = exportOptions.filter((opt) => !opt.featured);

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="mb-6">
          <h3 className="mb-2 text-lg font-semibold text-foreground">
            Exportar Documento
          </h3>
          <p className="text-sm text-muted-foreground">
            Formatos profissionais para integração e compartilhamento
          </p>
        </div>

        <div className="mb-6">
          <h4 className="mb-3 text-sm font-medium text-foreground">Formatos Recomendados</h4>
          <div className="grid gap-4 md:grid-cols-2">
            {featuredOptions.map((option) => {
              const Icon = option.icon;
              const isExporting = exporting === option.id;
              return (
                <Button
                  key={option.id}
                  onClick={() => handleExport(option.id)}
                  disabled={isExporting}
                  variant="outline"
                  className="h-auto justify-start gap-4 p-4 text-left transition-all hover:border-primary hover:bg-primary/5 disabled:opacity-50"
                >
                  <div className="rounded-lg bg-gradient-primary p-3">
                    <Icon className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-foreground">{option.label}</div>
                    <div className="text-xs text-muted-foreground">{option.description}</div>
                  </div>
                  {isExporting ? (
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  ) : (
                    <Download className="h-5 w-5 text-muted-foreground" />
                  )}
                </Button>
              );
            })}
          </div>
        </div>

        <div>
          <h4 className="mb-3 text-sm font-medium text-foreground">Outros Formatos</h4>
          <div className="grid gap-3 md:grid-cols-3">
            {otherOptions.map((option) => {
              const Icon = option.icon;
              const isExporting = exporting === option.id;
              return (
                <Button
                  key={option.id}
                  onClick={() => handleExport(option.id)}
                  disabled={isExporting}
                  variant="ghost"
                  className="h-auto justify-start gap-3 p-3 text-left transition-all hover:bg-muted disabled:opacity-50"
                >
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  <div className="flex-1">
                    <div className="text-sm font-medium text-foreground">{option.label}</div>
                  </div>
                  {isExporting && (
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                  )}
                </Button>
              );
            })}
          </div>
        </div>
      </Card>

      <Card className="border-primary/20 bg-primary/5 p-4">
        <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-foreground">
          <FileCode className="h-4 w-4" />
          API REST para Integração
        </h4>
        <p className="mb-3 text-sm text-muted-foreground">
          Integre o Strukturis com seus sistemas jurídicos e de RH via API REST.
        </p>
        <div className="space-y-2 text-xs text-muted-foreground">
          <p>
            <strong>Endpoints disponíveis:</strong>
          </p>
          <code className="block rounded bg-muted p-2 font-mono">
            POST /api/ocr-process - Processar documento
          </code>
          <code className="block rounded bg-muted p-2 font-mono">
            GET /api/document/:id - Obter resultado
          </code>
          <p className="mt-2">
            📖 Documentação completa e exemplos disponíveis em breve
          </p>
        </div>
      </Card>

      <div className="rounded-lg bg-muted p-4">
        <p className="text-sm text-muted-foreground">
          💡 <strong>Dicas de uso:</strong>
        </p>
        <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
          <li>• <strong>Excel:</strong> Ideal para análise de dados e tabelas múltiplas</li>
          <li>• <strong>Word:</strong> Perfeito para edição e formatação adicional</li>
          <li>• <strong>PDF:</strong> Melhor para arquivamento e compartilhamento oficial</li>
          <li>• <strong>JSON:</strong> Use para integração com sistemas e APIs</li>
        </ul>
      </div>
    </div>
  );
};
