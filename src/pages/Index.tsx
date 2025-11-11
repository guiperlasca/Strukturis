import { useState } from "react";
import { Header } from "@/components/Header";
import { FileUpload } from "@/components/FileUpload";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { FeaturesSection } from "@/components/FeaturesSection";
import { StatsSection } from "@/components/StatsSection";
import { UseCasesSection } from "@/components/UseCasesSection";
import { StepIndicator } from "@/components/StepIndicator";
import { TextEditor } from "@/components/TextEditor";
import { ExportOptions } from "@/components/ExportOptions";
import { processImage, processPDF } from "@/utils/ocr";
import { ProcessedDocument, ProcessStep, PageResult } from "@/types/document";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";

type ProcessState = "idle" | "processing" | "review" | "export";

const Index = () => {
  const [state, setState] = useState<ProcessState>("idle");
  const [currentStep, setCurrentStep] = useState<ProcessStep>("upload");
  const [completedSteps, setCompletedSteps] = useState<ProcessStep[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [currentPage, setCurrentPage] = useState<number>();
  const [totalPages, setTotalPages] = useState<number>();
  const [processedDoc, setProcessedDoc] = useState<ProcessedDocument | null>(null);

  const markStepComplete = (step: ProcessStep) => {
    setCompletedSteps((prev) => [...prev, step]);
  };

  const handleFileSelect = async (file: File) => {
    setState("processing");
    setCurrentStep("upload");
    setCompletedSteps([]);
    setProgress(0);
    setProcessedDoc(null);
    setCurrentPage(undefined);
    setTotalPages(undefined);

    try {
      // Step 1: Upload
      markStepComplete("upload");
      setCurrentStep("preprocessing");
      setStatus("Preparando documento...");
      setProgress(5);

      await new Promise((resolve) => setTimeout(resolve, 800));

      // Step 2: Preprocessing
      setStatus("Aplicando correções automáticas na imagem...");
      setProgress(15);
      await new Promise((resolve) => setTimeout(resolve, 1200));
      markStepComplete("preprocessing");

      // Step 3: OCR
      setCurrentStep("ocr");
      setStatus("Carregando modelo OCR com IA...");
      setProgress(25);
      await new Promise((resolve) => setTimeout(resolve, 1000));

      let result: { pages: PageResult[]; overallConfidence: number } | PageResult;

      if (file.type.includes("pdf")) {
        setStatus("Extraindo e processando páginas do PDF...");
        const pdfResult = await processPDF(file, (current, total) => {
          setCurrentPage(current);
          setTotalPages(total);
          setStatus(`Processando OCR - Página ${current} de ${total}...`);
          const pageProgress = 25 + ((current / total) * 40);
          setProgress(Math.round(pageProgress));
        });
        result = pdfResult;
      } else {
        setStatus("Executando OCR na imagem...");
        setProgress(50);
        const imageResult = await processImage(file);
        result = {
          pages: [imageResult],
          overallConfidence: imageResult.confidence,
        };
        setProgress(65);
      }

      markStepComplete("ocr");

      // Step 4: Extraction
      setCurrentStep("extraction");
      setStatus("Extraindo texto e detectando tabelas...");
      setProgress(75);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      markStepComplete("extraction");

      // Step 5: Review
      setCurrentStep("review");
      setStatus("Preparando para revisão...");
      setProgress(90);

      const doc: ProcessedDocument = {
        originalFile: file,
        pages: result.pages,
        overallConfidence: result.overallConfidence,
        totalPages: result.pages.length,
        processedAt: new Date(),
      };

      await new Promise((resolve) => setTimeout(resolve, 500));
      setProgress(100);
      setProcessedDoc(doc);
      setState("review");
      markStepComplete("review");

      toast.success("Documento processado com sucesso!");
    } catch (error) {
      console.error("Erro ao processar:", error);
      toast.error("Erro ao processar o documento. Tente novamente.");
      setState("idle");
      setCurrentStep("upload");
      setCompletedSteps([]);
    }
  };

  const handleSaveEdits = (updatedPages: PageResult[]) => {
    if (!processedDoc) return;

    const updatedDoc: ProcessedDocument = {
      ...processedDoc,
      pages: updatedPages,
    };

    setProcessedDoc(updatedDoc);
  };

  const handleGoToExport = () => {
    setCurrentStep("export");
    setState("export");
    markStepComplete("export");
  };

  const handleReset = () => {
    setState("idle");
    setCurrentStep("upload");
    setCompletedSteps([]);
    setProgress(0);
    setStatus("");
    setCurrentPage(undefined);
    setTotalPages(undefined);
    setProcessedDoc(null);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-8">
        <div className="mx-auto max-w-7xl">
          {/* Show step indicator during processing and review */}
          {state !== "idle" && (
            <StepIndicator currentStep={currentStep} completedSteps={completedSteps} />
          )}

          {/* Initial state - Landing page */}
          {state === "idle" && (
            <>
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
            </>
          )}

          {/* Processing state */}
          {state === "processing" && (
            <div className="mx-auto max-w-2xl">
              <ProcessingStatus
                progress={progress}
                status={status}
                currentPage={currentPage}
                totalPages={totalPages}
              />
            </div>
          )}

          {/* Review state */}
          {state === "review" && processedDoc && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-foreground">Revisão do Documento</h2>
                  <p className="text-muted-foreground">
                    Confiabilidade geral: <span className="font-semibold">{processedDoc.overallConfidence}%</span>
                  </p>
                </div>
                <div className="flex gap-3">
                  <Button onClick={handleReset} variant="outline" className="gap-2">
                    <RotateCcw className="h-4 w-4" />
                    Processar Novo
                  </Button>
                  <Button onClick={handleGoToExport} className="gap-2 bg-gradient-primary">
                    Prosseguir para Exportação
                  </Button>
                </div>
              </div>

              <TextEditor pages={processedDoc.pages} onSave={handleSaveEdits} />
            </div>
          )}

          {/* Export state */}
          {state === "export" && processedDoc && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-foreground">
                    Exportar Documento Processado
                  </h2>
                  <p className="text-muted-foreground">
                    {processedDoc.totalPages} página{processedDoc.totalPages > 1 ? "s" : ""} •{" "}
                    {processedDoc.overallConfidence}% confiabilidade
                  </p>
                </div>
                <Button onClick={handleReset} variant="outline" className="gap-2">
                  <RotateCcw className="h-4 w-4" />
                  Processar Novo Documento
                </Button>
              </div>

              <ExportOptions document={processedDoc} />
            </div>
          )}
        </div>
      </main>

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
