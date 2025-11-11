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
    const googleCredentialsJson = Deno.env.get("GOOGLE_APPLICATION_CREDENTIALS_JSON");

    if (!googleCredentialsJson) {
      throw new Error("GOOGLE_APPLICATION_CREDENTIALS_JSON not configured");
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

    // Get signed URL for Google Cloud Vision API access
    const { data: urlData } = await supabase.storage
      .from("documents")
      .createSignedUrl(storagePath, 3600); // 1 hour expiry

    if (!urlData?.signedUrl) {
      throw new Error("Failed to create signed URL for document");
    }

    console.log("Signed URL created for document access");

    // Use Google Cloud Vision API for OCR
    // First, get OAuth token from service account credentials
    const credentials = JSON.parse(googleCredentialsJson);
    
    // Create JWT for Google OAuth
    const header = {
      alg: "RS256",
      typ: "JWT",
      kid: credentials.private_key_id,
    };

    const now = Math.floor(Date.now() / 1000);
    const payload = {
      iss: credentials.client_email,
      scope: "https://www.googleapis.com/auth/cloud-platform",
      aud: "https://oauth2.googleapis.com/token",
      exp: now + 3600,
      iat: now,
    };

    // Import private key and sign
    const encoder = new TextEncoder();
    const keyData = credentials.private_key.replace(/-----BEGIN PRIVATE KEY-----|-----END PRIVATE KEY-----|\n/g, "");
    const binaryKey = Uint8Array.from(atob(keyData), c => c.charCodeAt(0));
    
    const cryptoKey = await crypto.subtle.importKey(
      "pkcs8",
      binaryKey,
      {
        name: "RSASSA-PKCS1-v1_5",
        hash: "SHA-256",
      },
      false,
      ["sign"]
    );

    const dataToSign = `${btoa(JSON.stringify(header))}.${btoa(JSON.stringify(payload))}`;
    const signature = await crypto.subtle.sign(
      "RSASSA-PKCS1-v1_5",
      cryptoKey,
      encoder.encode(dataToSign)
    );

    const jwt = `${dataToSign}.${btoa(String.fromCharCode(...new Uint8Array(signature)))}`;

    // Exchange JWT for access token
    const tokenResponse = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=${jwt}`,
    });

    const tokenData = await tokenResponse.json();
    const accessToken = tokenData.access_token;

    console.log("Google OAuth token obtained");

    // Determine pages to process
    let pagesToProcess: number[] = [];
    
    if (mimeType.includes('pdf')) {
      // For PDFs, use selected pages or default to first 5
      const maxPages = 5; // Limit for demo
      pagesToProcess = selectedPages && selectedPages.length > 0 
        ? selectedPages.slice(0, maxPages)
        : [1, 2, 3, 4, 5];
    } else {
      // For images, just one page
      pagesToProcess = [1];
    }
    
    console.log(`Will process pages: ${pagesToProcess.join(', ')}`);

    const pages = [];
    let overallConfidence = 0;

    for (const pageNum of pagesToProcess) {
      console.log(`Processing page ${pageNum} with Google Vision API...`);
      
      // Call Google Cloud Vision API for text detection
      const visionResponse = await fetch(
        `https://vision.googleapis.com/v1/images:annotate`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            requests: [{
              image: {
                source: {
                  imageUri: urlData.signedUrl,
                },
              },
              features: [{
                type: "DOCUMENT_TEXT_DETECTION",
                maxResults: 1,
              }],
            }],
          }),
        }
      );

      if (!visionResponse.ok) {
        console.error("Vision API error:", await visionResponse.text());
        throw new Error("Failed to process document with Google Vision API");
      }

      const visionData = await visionResponse.json();
      const textAnnotations = visionData.responses?.[0]?.textAnnotations;
      
      let rawText = "";
      let confidence = 0;

      if (textAnnotations && textAnnotations.length > 0) {
        rawText = textAnnotations[0].description || "";
        // Calculate average confidence from all text annotations
        const confidenceValues = textAnnotations
          .slice(1) // Skip first which is full text
          .map((a: any) => a.confidence || 0.9)
          .filter((c: number) => c > 0);
        
        confidence = confidenceValues.length > 0
          ? confidenceValues.reduce((sum: number, c: number) => sum + c, 0) / confidenceValues.length
          : 0.9;
      }

      console.log(`Page ${pageNum} extracted, confidence: ${confidence}, text length: ${rawText.length}`);
      
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
