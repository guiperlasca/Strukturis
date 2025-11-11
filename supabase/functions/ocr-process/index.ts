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
    console.log('OCR Process API - Received request');

    // Parse the request
    const contentType = req.headers.get('content-type') || '';
    
    if (!contentType.includes('multipart/form-data')) {
      return new Response(
        JSON.stringify({ 
          error: 'Content-Type must be multipart/form-data',
          message: 'Por favor, envie o arquivo como multipart/form-data'
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    // Parse form data
    const formData = await req.formData();
    const file = formData.get('file');
    const webhookUrl = formData.get('webhook_url') as string | null;

    if (!file || !(file instanceof File)) {
      return new Response(
        JSON.stringify({ 
          error: 'No file provided',
          message: 'Por favor, envie um arquivo PDF ou imagem'
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/webp',
    ];

    if (!allowedTypes.includes(file.type)) {
      return new Response(
        JSON.stringify({ 
          error: 'Invalid file type',
          message: 'Apenas arquivos PDF e imagens (JPG, PNG, WEBP) são aceitos',
          receivedType: file.type
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    // Validate file size (20MB max)
    const maxSize = 20 * 1024 * 1024; // 20MB
    if (file.size > maxSize) {
      return new Response(
        JSON.stringify({ 
          error: 'File too large',
          message: 'O arquivo deve ter no máximo 20MB',
          size: file.size,
          maxSize
        }),
        { 
          status: 400, 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
        }
      );
    }

    // Generate unique processing ID
    const processingId = crypto.randomUUID();
    
    console.log(`Processing ID: ${processingId}`);
    console.log(`File name: ${file.name}`);
    console.log(`File type: ${file.type}`);
    console.log(`File size: ${(file.size / 1024).toFixed(2)} KB`);

    // In a real implementation, you would:
    // 1. Store the file in Supabase Storage
    // 2. Queue the OCR processing job
    // 3. Return the processing ID immediately
    // 4. Process asynchronously and call webhook when done

    // For now, return a mock response
    const response = {
      success: true,
      processingId,
      status: 'processing',
      message: 'Documento recebido e em processamento',
      estimatedTime: '30-60 segundos',
      fileName: file.name,
      fileSize: file.size,
      webhookUrl: webhookUrl || null,
      _note: 'Esta é uma implementação de demonstração. Em produção, o processamento seria assíncrono.'
    };

    console.log('Response:', response);

    return new Response(
      JSON.stringify(response),
      { 
        status: 202, // Accepted
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );

  } catch (error) {
    console.error('Error in ocr-process:', error);
    const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
    return new Response(
      JSON.stringify({ 
        error: errorMessage,
        message: 'Erro ao processar documento'
      }),
      { 
        status: 500, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
  }
});
