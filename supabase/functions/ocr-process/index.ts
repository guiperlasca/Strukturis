import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface OCRRequest {
  storagePath: string;
  filename: string;
  mimeType: string;
  fileSize: number;
  userId: string;
  selectedPages?: number[];
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    const googleApiKey = Deno.env.get("GOOGLE_CLOUD_API_KEY");
    const lovableApiKey = Deno.env.get("LOVABLE_API_KEY");

    if (!googleApiKey) {
      throw new Error("GOOGLE_CLOUD_API_KEY not configured");
    }

    const supabase = createClient(supabaseUrl, supabaseKey);
    
    const { storagePath, filename, mimeType, fileSize, userId, selectedPages }: OCRRequest = await req.json();

    console.log("Processing OCR for:", { storagePath, filename, userId });

    const startTime = Date.now();

    // Create document record in database
    const { data: document, error: docError } = await supabase
      .from("ocr_documents")
      .insert({
        user_id: userId,
        original_filename: filename,
        storage_path: storagePath,
        file_size: fileSize,
        mime_type: mimeType,
        status: "processing",
      })
      .select()
      .single();

    if (docError) {
      console.error("Error creating document record:", docError);
      throw docError;
    }

    console.log("Document record created:", document.id);

    // Get file from storage and convert to base64
    const { data: fileData, error: downloadError } = await supabase.storage
      .from("documents")
      .download(storagePath);

    if (downloadError || !fileData) {
      console.error("Error downloading file:", downloadError);
      await supabase
        .from("ocr_documents")
        .update({ status: "failed", error_message: "Failed to download file" })
        .eq("id", document.id);
      throw new Error("Failed to download file from storage");
    }

    console.log("File downloaded successfully, size:", fileData.size);

    // Convert to base64 for Google Vision API
    const arrayBuffer = await fileData.arrayBuffer();
    const base64Content = btoa(
      String.fromCharCode(...new Uint8Array(arrayBuffer))
    );

    console.log("File converted to base64");

    // Determine pages to process
    let pagesToProcess: number[] = [];
    
    if (mimeType.includes('pdf')) {
      // For PDFs, use selected pages or default to first 3
      const maxPages = 3; // Reduced to avoid memory issues
      pagesToProcess = selectedPages && selectedPages.length > 0 
        ? selectedPages.slice(0, maxPages)
        : [1, 2, 3];
    } else {
      // For images, just one page
      pagesToProcess = [1];
    }
    
    console.log(`Will process ${pagesToProcess.length} page(s): ${pagesToProcess.join(', ')}`);

    let overallConfidence = 0;

    for (const pageNum of pagesToProcess) {
      console.log(`Processing page ${pageNum} with Google Vision API...`);
      
      // Call Google Cloud Vision API for text detection
      const visionResponse = await fetch(
        `https://vision.googleapis.com/v1/images:annotate?key=${googleApiKey}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            requests: [{
              image: {
                content: base64Content,
              },
              features: [{
                type: "DOCUMENT_TEXT_DETECTION",
              }],
            }],
          }),
        }
      );

      if (!visionResponse.ok) {
        const errorText = await visionResponse.text();
        console.error("Vision API error:", errorText);
        
        // Mark as failed and continue
        await supabase
          .from("ocr_documents")
          .update({ 
            status: "failed", 
            error_message: `Google Vision API error: ${errorText.substring(0, 200)}` 
          })
          .eq("id", document.id);
        
        throw new Error("Failed to process document with Google Vision API");
      }

      const visionData = await visionResponse.json();
      console.log("Vision API response received");
      
      const textAnnotations = visionData.responses?.[0]?.fullTextAnnotation;
      
      let rawText = "";
      let confidence = 0.9;

      if (textAnnotations) {
        rawText = textAnnotations.text || "";
        
        // Calculate average confidence from pages
        if (textAnnotations.pages && textAnnotations.pages.length > 0) {
          const confidenceValues = textAnnotations.pages
            .flatMap((p: any) => p.blocks || [])
            .flatMap((b: any) => b.paragraphs || [])
            .map((p: any) => p.confidence || 0.9)
            .filter((c: number) => c > 0);
          
          if (confidenceValues.length > 0) {
            confidence = confidenceValues.reduce((sum: number, c: number) => sum + c, 0) / confidenceValues.length;
          }
        }
      }

      console.log(`Page ${pageNum} extracted, confidence: ${(confidence * 100).toFixed(1)}%, text length: ${rawText.length}`);
      
      if (!rawText || rawText.trim().length === 0) {
        console.warn(`Page ${pageNum} has no text content`);
        rawText = `[Página ${pageNum} sem texto detectado]`;
      }
      
      const pageConfidence = confidence;
      overallConfidence += pageConfidence;

      // Apply contextual correction with Lovable AI
      let correctedText = rawText;
      if (lovableApiKey && rawText.trim()) {
        try {
          const aiResponse = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${lovableApiKey}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              model: "google/gemini-2.5-flash",
              messages: [
                {
                  role: "system",
                  content: "Você é um especialista em correção de texto OCR. Corrija erros típicos de OCR mantendo o significado original. Corrija datas, nomes, números e formatações. Retorne apenas o texto corrigido, sem explicações."
                },
                {
                  role: "user",
                  content: `Corrija este texto extraído por OCR:\n\n${rawText}`
                }
              ],
            }),
          });

          if (aiResponse.ok) {
            const aiResult = await aiResponse.json();
            correctedText = aiResult.choices?.[0]?.message?.content || rawText;
            console.log("AI correction applied successfully");
          } else {
            console.error("AI correction failed:", await aiResponse.text());
          }
        } catch (aiError) {
          console.error("AI correction error:", aiError);
        }
      }

      // Save page to database
      await supabase.from("ocr_pages").insert({
        document_id: document.id,
        page_number: pageNum,
        raw_text: rawText,
        corrected_text: correctedText,
        confidence: Math.round(pageConfidence * 100),
        has_table: false,
        table_data: null,
        detected_language: "pt",
      });
    }

    // Calculate final metrics
    const avgConfidence = pagesToProcess.length > 0 ? overallConfidence / pagesToProcess.length : 0;
    const processingTime = Date.now() - startTime;

    // Update document with final status
    await supabase
      .from("ocr_documents")
      .update({
        status: "completed",
        overall_confidence: Math.round(avgConfidence * 100),
        total_pages: pagesToProcess.length,
        processing_time_ms: processingTime,
        detected_language: "pt",
      })
      .eq("id", document.id);

    console.log("OCR processing completed successfully");

    return new Response(
      JSON.stringify({
        documentId: document.id,
        status: "completed",
        totalPages: pagesToProcess.length,
        confidence: Math.round(avgConfidence * 100),
        processingTime,
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      }
    );
  } catch (error) {
    console.error("Error in ocr-process:", error);
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      JSON.stringify({ 
        error: errorMessage,
        message: "Erro ao processar documento"
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, "Content-Type": "application/json" } 
      }
    );
  }
});
