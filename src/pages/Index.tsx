import { useState } from "react";
import { Header } from "@/components/Header";
import { FileUpload } from "@/components/FileUpload";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import { FeaturesSection } from "@/components/FeaturesSection";
import { StatsSection } from "@/components/StatsSection";
import { UseCasesSection } from "@/components/UseCasesSection";
import { processImage, processPDF } from "@/utils/ocr";
import { toast } from "sonner";

type ProcessState = "idle" | "processing" | "completed";

const Index = () => {
  const [state, setState] = useState<ProcessState>("idle");
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [currentPage, setCurrentPage] = useState<number>();
  const [totalPages, setTotalPages] = useState<number>();
  const [result, setResult] = useState<{ text: string; confidence: number; pages?: number } | null>(null);

  const handleFileSelect = async (file: File) => {
    setState("processing");
    setProgress(0);
    setResult(null);
    setCurrentPage(undefined);
    setTotalPages(undefined);

    try {
      setStatus("Carregando modelo OCR...");
      setProgress(10);

      await new Promise((resolve) => setTimeout(resolve, 1000));

      let extractedData;
      if (file.type.includes("pdf")) {
        setStatus("Extraindo páginas do PDF...");
        setProgress(20);

        extractedData = await processPDF(file, (current, total) => {
          setCurrentPage(current);
          setTotalPages(total);
          setStatus("Processando páginas...");
          // Progress from 20% to 90% based on page processing
          const pageProgress = 20 + ((current / total) * 70);
          setProgress(Math.round(pageProgress));
        });
      } else {
        setStatus("Processando imagem...");
        setProgress(50);
        extractedData = await processImage(file);
        setProgress(80);
      }

      setStatus("Finalizando extração...");
      setProgress(95);

      await new Promise((resolve) => setTimeout(resolve, 500));

      setProgress(100);
      setResult(extractedData);
      setState("completed");
      
      toast.success("Texto extraído com sucesso!");
    } catch (error) {
      console.error("Erro ao processar:", error);
      toast.error("Erro ao processar o documento. Tente novamente.");
      setState("idle");
    }
  };

  const handleReset = () => {
    setState("idle");
    setProgress(0);
    setStatus("");
    setCurrentPage(undefined);
    setTotalPages(undefined);
    setResult(null);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 py-12">
        <div className="mx-auto max-w-7xl">
          {state === "idle" && (
            <>
              <div className="mb-12 text-center">
                <h2 className="mb-4 text-4xl font-bold text-foreground">
                  Automatize a Transcrição de Documentos
                </h2>
                <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
                  Elimine a transcrição manual de PDFs digitalizados. 
                  Solução profissional para escritórios jurídicos, RH, contabilidade e empresas.
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

          {state === "completed" && result && (
            <div className="mx-auto max-w-4xl">
              <ResultsDisplay
                text={result.text}
                confidence={result.confidence}
                pages={result.pages}
                onReset={handleReset}
              />
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
