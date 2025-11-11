import { useState } from "react";
import { Header } from "@/components/Header";
import { FileUpload } from "@/components/FileUpload";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import { processImage, processPDF } from "@/utils/ocr";
import { toast } from "sonner";

type ProcessState = "idle" | "processing" | "completed";

const Index = () => {
  const [state, setState] = useState<ProcessState>("idle");
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [result, setResult] = useState<{ text: string; confidence: number } | null>(null);

  const handleFileSelect = async (file: File) => {
    setState("processing");
    setProgress(0);
    setResult(null);

    try {
      setStatus("Carregando modelo OCR...");
      setProgress(20);

      await new Promise((resolve) => setTimeout(resolve, 1000));

      setStatus("Processando documento...");
      setProgress(50);

      let extractedData;
      if (file.type.includes("pdf")) {
        extractedData = await processPDF(file);
      } else {
        extractedData = await processImage(file);
      }

      setProgress(80);
      setStatus("Finalizando extração...");

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
    setResult(null);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 py-12">
        <div className="mx-auto max-w-4xl">
          <div className="mb-8 text-center">
            <h2 className="mb-3 text-3xl font-bold text-foreground">
              Transforme Documentos Digitalizados em Texto
            </h2>
            <p className="text-lg text-muted-foreground">
              Upload de PDFs e imagens para extração inteligente com OCR e IA
            </p>
          </div>

          {state === "idle" && (
            <FileUpload onFileSelect={handleFileSelect} isProcessing={false} />
          )}

          {state === "processing" && (
            <ProcessingStatus progress={progress} status={status} />
          )}

          {state === "completed" && result && (
            <ResultsDisplay
              text={result.text}
              confidence={result.confidence}
              onReset={handleReset}
            />
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
