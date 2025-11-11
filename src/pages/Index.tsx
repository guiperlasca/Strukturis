import { useState } from "react";
import { Header } from "@/components/Header";
import { FileUpload } from "@/components/FileUpload";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { DocumentSidebar } from "@/components/DocumentSidebar";
import { SplitView } from "@/components/SplitView";
import { ExportOptions } from "@/components/ExportOptions";
import { ConfidenceReport } from "@/components/ConfidenceReport";
import { FeaturesSection } from "@/components/FeaturesSection";
import { StatsSection } from "@/components/StatsSection";
import { UseCasesSection } from "@/components/UseCasesSection";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { useOCRProcessor } from "@/hooks/useOCRProcessor";
import { ProcessedDocument } from "@/types/document";
import { toast } from "sonner";
import { RotateCcw, Download } from "lucide-react";

type AppState = "landing" | "processing" | "viewing";

const Index = () => {
  const [state, setState] = useState<AppState>("landing");
  const [processedDoc, setProcessedDoc] = useState<ProcessedDocument | null>(null);
  const [selectedPageNumber, setSelectedPageNumber] = useState(1);
  const [showReport, setShowReport] = useState(false);
  const [showExport, setShowExport] = useState(false);

  const { processDocument, isProcessing, progress } = useOCRProcessor();

  const handleFileSelect = async (file: File) => {
    setState("processing");
    setProcessedDoc(null);

    const result = await processDocument(file);
    
    if (result) {
      setProcessedDoc(result);
      setState("viewing");
      setSelectedPageNumber(1);
      toast.success("Documento processado com sucesso!");
    } else {
      setState("landing");
    }
  };

  const handlePageTextChange = (pageNumber: number, newText: string) => {
    if (!processedDoc) return;

    const updatedPages = processedDoc.pages.map((p) =>
      p.pageNumber === pageNumber ? { ...p, text: newText } : p
    );

    setProcessedDoc({
      ...processedDoc,
      pages: updatedPages,
    });
  };

  const handleSavePage = () => {
    toast.success("Alterações salvas!");
  };

  const handleReset = () => {
    setState("landing");
    setProcessedDoc(null);
    setSelectedPageNumber(1);
    setShowReport(false);
    setShowExport(false);
  };

  const currentPageData = processedDoc?.pages.find(
    (p) => p.pageNumber === selectedPageNumber
  );

  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Landing Page */}
      {state === "landing" && (
        <main className="container mx-auto px-4 py-12">
          <div className="mx-auto max-w-7xl">
            <div className="mb-12 text-center">
              <h2 className="mb-4 text-4xl font-bold text-foreground">
                Automatize a Transcrição de Documentos
              </h2>
              <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
                Elimine a transcrição manual de PDFs digitalizados. Solução profissional
                para escritórios jurídicos, RH, contabilidade e empresas.
              </p>
            </div>

            <StatsSection />

            <div className="my-12">
              <FileUpload onFileSelect={handleFileSelect} isProcessing={false} />
            </div>

            <FeaturesSection />
            <UseCasesSection />
          </div>
        </main>
      )}

      {/* Processing State */}
      {state === "processing" && (
        <main className="container mx-auto px-4 py-12">
          <div className="mx-auto max-w-2xl">
            <ProcessingStatus
              progress={progress}
              status="Processando documento com OCR profissional e correção por IA..."
            />
          </div>
        </main>
      )}

      {/* Viewing State with Sidebar */}
      {state === "viewing" && processedDoc && (
        <SidebarProvider>
          <div className="flex min-h-[calc(100vh-64px)] w-full">
            <DocumentSidebar
              pages={processedDoc.pages}
              currentPage={selectedPageNumber}
              onPageSelect={setSelectedPageNumber}
            />

            <main className="flex flex-1 flex-col">
              {/* Top Bar */}
              <div className="flex items-center justify-between border-b border-border bg-card px-6 py-4">
                <div className="flex items-center gap-4">
                  <SidebarTrigger />
                  <div>
                    <h1 className="text-lg font-semibold text-foreground">
                      {processedDoc.originalFile.name}
                    </h1>
                    <p className="text-sm text-muted-foreground">
                      {processedDoc.documentType?.icon} {processedDoc.documentType?.label} •{" "}
                      {processedDoc.totalPages} página{processedDoc.totalPages > 1 ? "s" : ""} •{" "}
                      {processedDoc.overallConfidence}% confiabilidade
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    onClick={() => {
                      setShowReport(!showReport);
                      setShowExport(false);
                    }}
                    variant={showReport ? "default" : "outline"}
                  >
                    {showReport ? "Ocultar" : "Ver"} Relatório
                  </Button>
                  <Button
                    onClick={() => {
                      setShowExport(!showExport);
                      setShowReport(false);
                    }}
                    variant={showExport ? "default" : "outline"}
                    className="gap-2"
                  >
                    <Download className="h-4 w-4" />
                    Exportar
                  </Button>
                  <Button onClick={handleReset} variant="outline" className="gap-2">
                    <RotateCcw className="h-4 w-4" />
                    Novo Documento
                  </Button>
                </div>
              </div>

              {/* Content Area */}
              <div className="flex-1 overflow-auto p-6">
                {showReport ? (
                  <ConfidenceReport document={processedDoc} />
                ) : showExport ? (
                  <ExportOptions document={processedDoc} />
                ) : currentPageData ? (
                  <SplitView
                    page={currentPageData}
                    onTextChange={(text) =>
                      handlePageTextChange(selectedPageNumber, text)
                    }
                    onSave={handleSavePage}
                  />
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">
                    Página não encontrada
                  </div>
                )}
              </div>
            </main>
          </div>
        </SidebarProvider>
      )}

      <footer className="border-t border-border py-8">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm text-muted-foreground">
            Strukturis - OCR Avançado com Inteligência Artificial
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
