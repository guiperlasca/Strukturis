import { useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";
import type { ProcessedDocument } from "@/types/document";

export const useOCRProcessor = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentDocument, setCurrentDocument] = useState<ProcessedDocument | null>(null);

  const processDocument = async (
    file: File,
    pagesMode: 'all' | 'count' | 'custom',
    options?: { pagesCount?: number; pagesList?: number[] }
  ): Promise<ProcessedDocument | null> => {
    try {
      console.log("Starting document processing...", { 
        fileName: file.name, 
        fileSize: file.size, 
        pagesMode,
        options 
      });
      
      // Validate file size (20MB limit for Document AI)
      const MAX_FILE_SIZE = 20 * 1024 * 1024;
      if (file.size > MAX_FILE_SIZE) {
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const maxSizeMB = (MAX_FILE_SIZE / (1024 * 1024)).toFixed(0);
        toast.error(`Arquivo muito grande: ${fileSizeMB}MB. Limite: ${maxSizeMB}MB.`);
        return null;
      }
      
      setIsProcessing(true);
      setProgress(10);
      
      // Get current user
      const { data: { user }, error: authError } = await supabase.auth.getUser();
      
      if (!user) {
        console.error("User not authenticated");
        toast.error("Você precisa estar autenticado para processar documentos");
        return null;
      }

      // Upload to storage
      setProgress(20);
      const filePath = `${user.id}/${Date.now()}_${file.name}`;
      console.log("Uploading to storage:", filePath);
      
      const { error: uploadError, data: uploadData } = await supabase.storage
        .from("documents")
        .upload(filePath, file);

      if (uploadError) {
        console.error("Upload error:", uploadError);
        toast.error(`Erro ao fazer upload: ${uploadError.message}`);
        return null;
      }

      const { data: urlData } = supabase.storage
        .from("documents")
        .getPublicUrl(filePath);

      console.log("File uploaded successfully");
      setProgress(40);

      // Get auth token
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        toast.error("Sessão expirada");
        return null;
      }

      // Call Document AI processing edge function
      console.log("Calling process-document function...");
      setProgress(50);

      const { data, error } = await supabase.functions.invoke("process-document", {
        body: {
          fileUrl: urlData.publicUrl,
          mimeType: file.type,
          pagesMode,
          pagesCount: options?.pagesCount,
          pagesList: options?.pagesList,
          export: {
            json: true,
            csv: true,
          },
        },
      });

      if (error) {
        console.error("Processing error:", error);
        toast.error(`Erro ao processar documento: ${error.message || 'Erro desconhecido'}`);
        return null;
      }

      console.log("Processing response:", data);
      setProgress(90);

      // Transform to ProcessedDocument format
      const processedDoc: ProcessedDocument = {
        originalFile: file,
        pages: data.pages.map((page: any) => ({
          pageNumber: page.page,
          text: page.text,
          segments: [{
            text: page.text,
            confidence: page.confidence,
            startIndex: 0,
            endIndex: page.text.length,
          }],
          confidence: page.confidence,
          hasTable: page.tables.length > 0,
          tableData: page.tables.length > 0 ? page.tables[0].rows : undefined,
          language: 'pt-BR',
          status: page.status,
          qualityHints: page.qualityHints,
          tables: page.tables,
          entities: page.entities,
        })),
        overallConfidence: data.summary.readabilityConfidence,
        totalPages: data.pagesProcessed.length,
        processedAt: new Date(),
        processingTime: 0,
        detectedLanguage: 'pt-BR',
        summary: data.summary,
        exports: data.exports,
      };

      setProgress(100);
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
