import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { segment, context, documentType } = await req.json();
    
    if (!segment) {
      return new Response(
        JSON.stringify({ error: "Segment is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    console.log("Generating fill suggestions for illegible text...");

    const LOVABLE_API_KEY = Deno.env.get("LOVABLE_API_KEY");
    if (!LOVABLE_API_KEY) {
      throw new Error("LOVABLE_API_KEY not configured");
    }

    const documentTypeHint = documentType 
      ? `\nEste é um documento do tipo: ${documentType}` 
      : "";

    const response = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${LOVABLE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-2.5-flash",
        messages: [
          {
            role: "system",
            content: `Você é um assistente especializado em sugerir preenchimentos para trechos ilegíveis de documentos OCR em português brasileiro.
Baseando-se no contexto fornecido, sugira 3 opções plausíveis para o trecho ilegível.${documentTypeHint}

Retorne as sugestões em formato JSON:
{
  "suggestions": [
    { "text": "sugestão 1", "confidence": 0.8 },
    { "text": "sugestão 2", "confidence": 0.6 },
    { "text": "sugestão 3", "confidence": 0.4 }
  ]
}

Baseie-se em:
- Contexto do documento
- Tipo de documento
- Padrões comuns em documentos brasileiros
- Lógica e coerência textual`
          },
          {
            role: "user",
            content: `Contexto anterior: ${context.before || "Início do documento"}
            
Trecho ilegível: ${segment}

Contexto posterior: ${context.after || "Fim do documento"}

Sugira 3 opções plausíveis para o trecho ilegível.`
          }
        ],
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("AI API error:", response.status, errorText);
      
      if (response.status === 429) {
        return new Response(
          JSON.stringify({ error: "Rate limit exceeded." }),
          { status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
      
      if (response.status === 402) {
        return new Response(
          JSON.stringify({ error: "AI credits depleted." }),
          { status: 402, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }

      throw new Error(`AI API returned ${response.status}`);
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || "{}";
    
    // Try to parse JSON from response
    let suggestions;
    try {
      suggestions = JSON.parse(content);
    } catch {
      // If AI didn't return valid JSON, create fallback suggestions
      suggestions = {
        suggestions: [
          { text: segment, confidence: 0.5 },
          { text: "[ilegível]", confidence: 0.3 },
          { text: "...", confidence: 0.2 }
        ]
      };
    }

    console.log("Suggestions generated successfully");

    return new Response(
      JSON.stringify(suggestions),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (error) {
    console.error("Error in ai-suggest-fill:", error);
    const errorMessage = error instanceof Error ? error.message : "Internal server error";
    return new Response(
      JSON.stringify({ error: errorMessage }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
