import { pipeline, env } from "@huggingface/transformers";

// Configure transformers to use browser cache
env.allowLocalModels = false;
env.useBrowserCache = true;

let ocrPipeline: any = null;

export const initializeOCR = async () => {
  if (!ocrPipeline) {
    console.log("Inicializando modelo OCR...");
    ocrPipeline = await pipeline(
      "image-to-text",
      "Xenova/trocr-small-printed"
    );
    console.log("Modelo OCR carregado!");
  }
  return ocrPipeline;
};

export const processImage = async (imageFile: File): Promise<{ text: string; confidence: number }> => {
  try {
    const pipeline = await initializeOCR();
    
    // Convert file to data URL
    const reader = new FileReader();
    const imageUrl = await new Promise<string>((resolve) => {
      reader.onload = (e) => resolve(e.target?.result as string);
      reader.readAsDataURL(imageFile);
    });

    console.log("Processando imagem com OCR...");
    const result = await pipeline(imageUrl);
    
    console.log("Resultado OCR:", result);
    
    // Extract text from result
    const text = result[0]?.generated_text || "";
    
    // Calculate confidence (mock implementation - you can enhance this)
    const confidence = text.length > 0 ? Math.min(95, 75 + Math.random() * 20) : 50;
    
    return {
      text,
      confidence: Math.round(confidence),
    };
  } catch (error) {
    console.error("Erro no OCR:", error);
    throw new Error("Falha ao processar a imagem");
  }
};

export const processPDF = async (pdfFile: File): Promise<{ text: string; confidence: number }> => {
  // For PDFs, we'll need to convert to images first
  // This is a simplified version - in production, you'd use PDF.js to render pages
  console.log("Processando PDF...");
  
  // Mock implementation for now
  return {
    text: "Processamento de PDF será implementado com PDF.js para converter páginas em imagens.",
    confidence: 75,
  };
};
