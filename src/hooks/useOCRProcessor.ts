import { useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import type { ProcessedDocument } from "@/types/document";

export const useOCRProcessor = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentDocument, setCurrentDocument] = useState<ProcessedDocument | null>(null);

  const processDocument = async (file: File): Promise<ProcessedDocument | null> => {
    try {
      setIsProcessing(true);
      setProgress(10);
      
      // Get current user
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        toast.error("Você precisa estar autenticado para processar documentos");
        return null;
      }

      const startTime = Date.now();

      // Upload to storage
      setProgress(20);
      const filePath = `${user.id}/${Date.now()}_${file.name}`;
      const { error: uploadError } = await supabase.storage
        .from("documents")
        .upload(filePath, file);

      if (uploadError) {
        console.error("Upload error:", uploadError);
        toast.error("Erro ao fazer upload do arquivo");
        return null;
      }

      setProgress(40);

      // Call OCR processing edge function
      const { data, error } = await supabase.functions.invoke("ocr-process", {
        body: {
          storagePath: filePath,
          filename: file.name,
          mimeType: file.type,
          fileSize: file.size,
          userId: user.id,
        },
      });

      if (error) {
        console.error("OCR processing error:", error);
        toast.error("Erro ao processar documento");
        return null;
      }

      setProgress(80);

      // Fetch complete document data
      const { data: documentData, error: fetchError } = await supabase
        .from("ocr_documents")
        .select(`
          *,
          ocr_pages (*)
        `)
        .eq("id", data.documentId)
        .single();

      if (fetchError) {
        console.error("Error fetching document:", fetchError);
        toast.error("Erro ao recuperar dados do documento");
        return null;
      }

      setProgress(100);

      // Transform to ProcessedDocument format
      const processedDoc: ProcessedDocument = {
        originalFile: file,
        pages: documentData.ocr_pages.map((page: any) => ({
          pageNumber: page.page_number,
          text: page.corrected_text || page.raw_text,
          segments: [{
            text: page.corrected_text || page.raw_text,
            confidence: page.confidence,
            startIndex: 0,
            endIndex: (page.corrected_text || page.raw_text).length,
          }],
          confidence: page.confidence,
          hasTable: page.has_table,
          tableData: page.table_data,
          language: page.detected_language,
        })),
        overallConfidence: documentData.overall_confidence,
        totalPages: documentData.total_pages,
        processedAt: new Date(documentData.completed_at),
        processingTime: documentData.processing_time_ms,
        detectedLanguage: documentData.detected_language,
      };

      setCurrentDocument(processedDoc);
      toast.success("Documento processado com sucesso!");
      
      return processedDoc;
    } catch (error) {
      console.error("Processing error:", error);
      toast.error("Erro ao processar documento");
      return null;
    } finally {
      setIsProcessing(false);
      setProgress(0);
    }
  };

  return {
    processDocument,
    isProcessing,
    progress,
    currentDocument,
  };
};
