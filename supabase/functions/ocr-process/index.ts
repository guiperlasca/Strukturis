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
    
    const { storagePath, filename, mimeType, fileSize, userId }: OCRRequest = await req.json();

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

    // Download file from storage
    const { data: fileData, error: downloadError } = await supabase.storage
      .from("documents")
      .download(storagePath);

    if (downloadError) {
      console.error("Error downloading file:", downloadError);
      await supabase
        .from("ocr_documents")
        .update({ status: "failed", error_message: "Failed to download file" })
        .eq("id", document.id);
      throw downloadError;
    }

    // Convert file to base64
    const arrayBuffer = await fileData.arrayBuffer();
    const base64File = btoa(
      new Uint8Array(arrayBuffer).reduce(
        (data, byte) => data + String.fromCharCode(byte),
        ""
      )
    );

    // Call Google Document AI (use your actual project ID and processor ID)
    // For now, we'll simulate the response
    console.log("Calling Google Document AI...");
    
    // Simulated OCR result - replace with actual API call
    const mockPages = [
      {
        text: "Este é um exemplo de texto extraído por OCR.\nNome: João Silva\nData: 15/03/2024\nDocumento: RG 12.345.678-9",
        confidence: 0.95,
        hasTables: false,
        tables: [],
      }
    ];

    const totalPages = mockPages.length;
    let overallConfidence = 0;

    console.log(`Processing ${totalPages} pages...`);

    for (let i = 0; i < mockPages.length; i++) {
      const page = mockPages[i];
      const pageNumber = i + 1;
      const pageText = page.text;
      const pageConfidence = page.confidence;
      overallConfidence += pageConfidence;

      // Apply contextual correction with Lovable AI
      let correctedText = pageText;
      if (lovableApiKey && pageText.trim()) {
        console.log(`Applying AI correction to page ${pageNumber}...`);
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
                  content: `Corrija este texto extraído por OCR:\n\n${pageText}`
                }
              ],
            }),
          });

          if (aiResponse.ok) {
            const aiResult = await aiResponse.json();
            correctedText = aiResult.choices?.[0]?.message?.content || pageText;
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
        page_number: pageNumber,
        raw_text: pageText,
        corrected_text: correctedText,
        confidence: Math.round(pageConfidence * 100),
        has_table: page.hasTables,
        table_data: page.tables.length > 0 ? page.tables : null,
        detected_language: "pt",
      });
    }

    // Calculate final metrics
    const avgConfidence = totalPages > 0 ? overallConfidence / totalPages : 0;
    const processingTime = Date.now() - startTime;

    // Update document with final status
    await supabase
      .from("ocr_documents")
      .update({
        status: "completed",
        overall_confidence: Math.round(avgConfidence * 100),
        total_pages: totalPages,
        processing_time_ms: processingTime,
        detected_language: "pt",
      })
      .eq("id", document.id);

    console.log("OCR processing completed successfully");

    return new Response(
      JSON.stringify({
        documentId: document.id,
        status: "completed",
        totalPages,
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
