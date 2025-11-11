import * as pdfjsLib from "pdfjs-dist";

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

export interface PDFPage {
  pageNumber: number;
  imageData: string;
  width: number;
  height: number;
}

export const extractPDFPages = async (file: File): Promise<PDFPage[]> => {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    const pages: PDFPage[] = [];

    console.log(`PDF carregado: ${pdf.numPages} páginas`);

    // Process first 10 pages (limit for performance)
    const maxPages = Math.min(pdf.numPages, 10);

    for (let pageNum = 1; pageNum <= maxPages; pageNum++) {
      const page = await pdf.getPage(pageNum);
      const viewport = page.getViewport({ scale: 2.0 });

      // Create canvas to render page
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      
      if (!context) {
        throw new Error("Failed to get canvas context");
      }

      canvas.width = viewport.width;
      canvas.height = viewport.height;

      // Render PDF page to canvas
      await page.render({
        canvasContext: context,
        viewport: viewport,
      } as any).promise;

      // Convert canvas to base64 image
      const imageData = canvas.toDataURL("image/png");

      pages.push({
        pageNumber: pageNum,
        imageData,
        width: viewport.width,
        height: viewport.height,
      });

      console.log(`Página ${pageNum} renderizada`);
    }

    return pages;
  } catch (error) {
    console.error("Erro ao processar PDF:", error);
    throw new Error("Falha ao extrair páginas do PDF");
  }
};

export const convertImageToDataURL = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target?.result) {
        resolve(e.target.result as string);
      } else {
        reject(new Error("Failed to read file"));
      }
    };
    reader.onerror = () => reject(new Error("Failed to read file"));
    reader.readAsDataURL(file);
  });
};
