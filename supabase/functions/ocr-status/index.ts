import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    // Get processing ID from URL
    const url = new URL(req.url);
    const processingId = url.pathname.split('/').pop();

    if (!processingId || processingId === 'ocr-status') {
      return new Response(
        JSON.stringify({ 
          error: 'Processing ID required',
          message: 'Por favor, forneça um ID de processamento válido'
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    console.log(`Checking status for processing ID: ${processingId}`);

    // In a real implementation, you would:
    // 1. Query the database for the processing status
    // 2. Return the current status and results if completed

    // Mock response for demonstration
    const mockResult = {
      processingId,
      status: 'completed',
      progress: 100,
      document: {
        fileName: 'documento.pdf',
        processedAt: new Date().toISOString(),
        overallConfidence: 94,
        totalPages: 3,
        processingTime: 45230,
        documentType: {
          type: 'contract',
          label: 'Contrato',
          confidence: 92,
          icon: '📄'
        },
        detectedLanguage: 'pt-BR'
      },
      pages: [
        {
          pageNumber: 1,
          text: 'Texto extraído da página 1...',
          confidence: 95,
          hasTable: false,
          segments: []
        },
        {
          pageNumber: 2,
          text: 'Texto extraído da página 2...',
          confidence: 93,
          hasTable: true,
          tableData: [
            ['Coluna 1', 'Coluna 2'],
            ['Dado 1', 'Dado 2']
          ],
          segments: []
        },
        {
          pageNumber: 3,
          text: 'Texto extraído da página 3...',
          confidence: 94,
          hasTable: false,
          segments: []
        }
      ],
      _note: 'Esta é uma resposta de demonstração. Em produção, os dados viriam do processamento real.'
    };

    return new Response(
      JSON.stringify(mockResult),
      { 
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );

  } catch (error) {
    console.error('Error in ocr-status:', error);
    const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
    return new Response(
      JSON.stringify({ 
        error: errorMessage,
        message: 'Erro ao consultar status do processamento'
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
});
