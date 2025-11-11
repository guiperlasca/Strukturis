import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.81.1";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface ProcessRequest {
  fileUrl: string;
  mimeType: string;
  pagesMode: 'all' | 'count' | 'custom';
  pagesCount?: number;
  pagesList?: number[];
  export?: {
    json?: boolean;
    csv?: boolean;
  };
}

interface QualityHint {
  type: string;
  severity: string;
}

interface TableData {
  name: string;
  confidence: number;
  rows: string[][];
}

interface Entity {
  field: string;
  value: string;
  confidence: number;
}

interface PageResult {
  page: number;
  status: 'ok' | 'low_quality' | 'error';
  qualityHints: string[];
  text: string;
  tables: TableData[];
  entities: Entity[];
  confidence: number;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Get auth user
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      return new Response(JSON.stringify({ error: 'Authorization required' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const token = authHeader.replace('Bearer ', '');
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);

    if (authError || !user) {
      return new Response(JSON.stringify({ error: 'Invalid token' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const body: ProcessRequest = await req.json();
    const { fileUrl, mimeType, pagesMode, pagesCount, pagesList, export: exportOptions } = body;

    console.log('Processing document:', { fileUrl, mimeType, pagesMode, user: user.id });

    // Validate input
    if (!fileUrl || !mimeType || !pagesMode) {
      return new Response(JSON.stringify({ error: 'Missing required fields' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Get Document AI credentials
    const credentialsJson = Deno.env.get('GOOGLE_APPLICATION_CREDENTIALS_JSON');
    const projectId = Deno.env.get('DOCAI_PROJECT_ID');
    const location = Deno.env.get('DOCAI_LOCATION') || 'us';
    const processorId = Deno.env.get('DOCAI_PROCESSOR_ID');

    if (!credentialsJson || !projectId || !processorId) {
      console.error('Missing Document AI configuration');
      return new Response(
        JSON.stringify({ error: 'Document AI not configured' }),
        { status: 502, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const credentials = JSON.parse(credentialsJson);

    // Download file from storage
    const { data: fileData, error: downloadError } = await supabase.storage
      .from('documents')
      .download(fileUrl.replace(/^.*\/documents\//, ''));

    if (downloadError || !fileData) {
      console.error('File download error:', downloadError);
      return new Response(JSON.stringify({ error: 'File not found or invalid URL' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const fileSize = fileData.size;
    const MAX_SIZE = 20 * 1024 * 1024; // 20MB limit for Document AI

    if (fileSize > MAX_SIZE) {
      return new Response(
        JSON.stringify({ error: `File size ${(fileSize / 1024 / 1024).toFixed(2)}MB exceeds 20MB limit` }),
        { status: 413, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Convert file to base64
    const arrayBuffer = await fileData.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);
    const chunkSize = 8192;
    let binaryString = '';
    
    for (let i = 0; i < bytes.length; i += chunkSize) {
      const chunk = bytes.slice(i, i + chunkSize);
      binaryString += String.fromCharCode(...chunk);
    }
    
    const base64Content = btoa(binaryString);

    // Get OAuth token
    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        assertion: await createJWT(credentials),
      }),
    });

    if (!tokenResponse.ok) {
      console.error('OAuth token error:', await tokenResponse.text());
      return new Response(
        JSON.stringify({ error: 'Failed to authenticate with Google' }),
        { status: 502, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const { access_token } = await tokenResponse.json();

    // Create document record
    const { data: docData, error: docError } = await supabase
      .from('documents')
      .insert({
        user_id: user.id,
        original_url: fileUrl,
        mime_type: mimeType,
        status: 'processing',
      })
      .select()
      .single();

    if (docError) {
      console.error('Document creation error:', docError);
      return new Response(JSON.stringify({ error: 'Failed to create document record' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    const documentId = docData.id;

    // Call Document AI
    const processorEndpoint = `https://${location}-documentai.googleapis.com/v1/projects/${projectId}/locations/${location}/processors/${processorId}:process`;

    const docAIResponse = await fetch(processorEndpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${access_token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        rawDocument: {
          content: base64Content,
          mimeType: mimeType,
        },
        processOptions: {
          ocrConfig: {
            enableNativePdfParsing: true,
            enableImageQualityScores: true,
            computeStyleInfo: true,
          },
        },
      }),
    });

    if (!docAIResponse.ok) {
      const errorText = await docAIResponse.text();
      console.error('Document AI error:', errorText);
      
      await supabase
        .from('documents')
        .update({ status: 'failed' })
        .eq('id', documentId);

      return new Response(
        JSON.stringify({ error: 'Document AI processing failed', details: errorText }),
        { status: 502, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const docAIResult = await docAIResponse.json();
    const document = docAIResult.document;

    // Determine pages to process
    const totalPages = document.pages?.length || 0;
    let pagesToProcess: number[] = [];

    if (pagesMode === 'all') {
      pagesToProcess = Array.from({ length: totalPages }, (_, i) => i + 1);
    } else if (pagesMode === 'count' && pagesCount) {
      pagesToProcess = Array.from({ length: Math.min(pagesCount, totalPages) }, (_, i) => i + 1);
    } else if (pagesMode === 'custom' && pagesList) {
      pagesToProcess = pagesList.filter(p => p >= 1 && p <= totalPages);
    }

    console.log('Processing pages:', pagesToProcess);

    // Process each page
    const pageResults: PageResult[] = [];
    let totalConfidence = 0;
    let successCount = 0;

    for (const pageNum of pagesToProcess) {
      const pageIndex = pageNum - 1;
      const page = document.pages[pageIndex];

      if (!page) continue;

      // Extract text
      const pageText = extractPageText(document, page);
      
      // Calculate confidence
      const confidence = calculatePageConfidence(page);
      totalConfidence += confidence;

      // Detect quality issues
      const qualityHints = detectQualityIssues(page);
      const status = qualityHints.length > 0 ? 'low_quality' : 'ok';
      if (status === 'ok') successCount++;

      // Extract tables
      const tables = extractTables(page, pageIndex);

      // Extract entities
      const entities = extractEntities(document, pageIndex);

      const pageResult: PageResult = {
        page: pageNum,
        status,
        qualityHints,
        text: pageText,
        tables,
        entities,
        confidence,
      };

      pageResults.push(pageResult);

      // Save to database
      await supabase.from('document_pages').insert({
        document_id: documentId,
        page: pageNum,
        status,
        confidence,
        quality_hints: qualityHints,
        text: pageText,
        tables: tables,
        entities: entities,
      });
    }

    // Calculate metrics
    const readabilityConfidence = pagesToProcess.length > 0 
      ? totalConfidence / pagesToProcess.length 
      : 0;
    const pageSuccessRate = pagesToProcess.length > 0 
      ? (successCount / pagesToProcess.length) * 100 
      : 0;
    const tablesDetected = pageResults.reduce((sum, p) => sum + p.tables.length, 0);
    const fieldsDetected = pageResults.reduce((sum, p) => sum + p.entities.length, 0);

    // Update document status
    await supabase
      .from('documents')
      .update({
        total_pages: totalPages,
        status: 'completed',
      })
      .eq('id', documentId);

    // Handle exports
    const exports: { jsonUrl?: string; csvUrl?: string } = {};

    if (exportOptions?.json) {
      const jsonData = JSON.stringify({ documentId, pageResults, summary: { readabilityConfidence, pageSuccessRate, tablesDetected, fieldsDetected } }, null, 2);
      const jsonPath = `${user.id}/processed/${documentId}.json`;
      
      await supabase.storage
        .from('documents')
        .upload(jsonPath, new Blob([jsonData], { type: 'application/json' }), { upsert: true });
      
      const { data: jsonUrl } = supabase.storage.from('documents').getPublicUrl(jsonPath);
      exports.jsonUrl = jsonUrl.publicUrl;
    }

    if (exportOptions?.csv && tablesDetected > 0) {
      const csvData = generateCSV(pageResults);
      const csvPath = `${user.id}/processed/${documentId}.csv`;
      
      await supabase.storage
        .from('documents')
        .upload(csvPath, new Blob([csvData], { type: 'text/csv' }), { upsert: true });
      
      const { data: csvUrl } = supabase.storage.from('documents').getPublicUrl(csvPath);
      exports.csvUrl = csvUrl.publicUrl;
    }

    // Save exports
    if (exports.jsonUrl || exports.csvUrl) {
      await supabase.from('document_exports').insert({
        document_id: documentId,
        json_url: exports.jsonUrl,
        csv_url: exports.csvUrl,
      });
    }

    return new Response(
      JSON.stringify({
        documentId,
        pagesProcessed: pagesToProcess,
        summary: {
          readabilityConfidence: Math.round(readabilityConfidence),
          pageSuccessRate: Math.round(pageSuccessRate),
          tablesDetected,
          fieldsDetected,
        },
        pages: pageResults,
        exports,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

// Helper functions
function extractPageText(document: any, page: any): string {
  const getText = (segment: any) => {
    if (!segment.layout?.textAnchor?.textSegments) return '';
    return segment.layout.textAnchor.textSegments
      .map((s: any) => {
        const start = parseInt(s.startIndex || '0');
        const end = parseInt(s.endIndex || '0');
        return document.text?.substring(start, end) || '';
      })
      .join('');
  };

  if (page.paragraphs) {
    return page.paragraphs.map(getText).join('\n');
  }
  
  if (page.lines) {
    return page.lines.map(getText).join('\n');
  }

  return '';
}

function calculatePageConfidence(page: any): number {
  if (!page.detectedLanguages?.[0]?.confidence) return 70;
  
  const langConfidence = page.detectedLanguages[0].confidence * 100;
  const qualityScore = page.quality?.qualityScore || 0.7;
  
  return (langConfidence * 0.7 + qualityScore * 100 * 0.3);
}

function detectQualityIssues(page: any): string[] {
  const hints: string[] = [];
  
  if (page.transforms) {
    page.transforms.forEach((t: any) => {
      if (Math.abs(t.rows?.[0]?.[1] || 0) > 0.1) hints.push('skew');
    });
  }
  
  const qualityScore = page.quality?.qualityScore || 1;
  if (qualityScore < 0.5) hints.push('blur');
  if (qualityScore < 0.3) hints.push('shadow');
  
  return hints;
}

function extractTables(page: any, pageIndex: number): TableData[] {
  if (!page.tables) return [];
  
  return page.tables.map((table: any, idx: number) => {
    const rows: string[][] = [];
    
    if (table.headerRows) {
      table.headerRows.forEach((row: any) => {
        const cells = row.cells?.map((cell: any) => cell.layout?.textAnchor?.content || '') || [];
        rows.push(cells);
      });
    }
    
    if (table.bodyRows) {
      table.bodyRows.forEach((row: any) => {
        const cells = row.cells?.map((cell: any) => cell.layout?.textAnchor?.content || '') || [];
        rows.push(cells);
      });
    }
    
    return {
      name: `table_${pageIndex + 1}_${idx + 1}`,
      confidence: table.detectionConfidence ? table.detectionConfidence * 100 : 85,
      rows,
    };
  });
}

function extractEntities(document: any, pageIndex: number): Entity[] {
  if (!document.entities) return [];
  
  return document.entities
    .filter((entity: any) => {
      const pageRefs = entity.pageAnchor?.pageRefs || [];
      return pageRefs.some((ref: any) => parseInt(ref.page || '0') === pageIndex);
    })
    .map((entity: any) => ({
      field: entity.type || 'unknown',
      value: entity.mentionText || '',
      confidence: entity.confidence ? entity.confidence * 100 : 0,
    }));
}

function generateCSV(pageResults: PageResult[]): string {
  const rows: string[][] = [['Page', 'Table', 'Row', ...Array(20).fill('').map((_, i) => `Col${i + 1}`)]];
  
  pageResults.forEach(page => {
    page.tables.forEach(table => {
      table.rows.forEach((row, rowIdx) => {
        const csvRow = [
          page.page.toString(),
          table.name,
          (rowIdx + 1).toString(),
          ...row.map(cell => `"${cell.replace(/"/g, '""')}"`),
        ];
        rows.push(csvRow);
      });
    });
  });
  
  return rows.map(row => row.join(',')).join('\n');
}

async function createJWT(credentials: any): Promise<string> {
  const header = { alg: 'RS256', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    iss: credentials.client_email,
    scope: 'https://www.googleapis.com/auth/cloud-platform',
    aud: 'https://oauth2.googleapis.com/token',
    exp: now + 3600,
    iat: now,
  };

  const encodedHeader = base64UrlEncode(JSON.stringify(header));
  const encodedPayload = base64UrlEncode(JSON.stringify(payload));
  const signatureInput = `${encodedHeader}.${encodedPayload}`;

  const privateKey = credentials.private_key;
  const signature = await signWithRSA(signatureInput, privateKey);
  
  return `${signatureInput}.${signature}`;
}

function base64UrlEncode(str: string): string {
  return btoa(str)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

async function signWithRSA(data: string, privateKey: string): Promise<string> {
  const pemHeader = '-----BEGIN PRIVATE KEY-----';
  const pemFooter = '-----END PRIVATE KEY-----';
  const pemContents = privateKey.substring(
    pemHeader.length,
    privateKey.length - pemFooter.length
  ).replace(/\s/g, '');

  const binaryDer = Uint8Array.from(atob(pemContents), c => c.charCodeAt(0));

  const cryptoKey = await crypto.subtle.importKey(
    'pkcs8',
    binaryDer,
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const encoder = new TextEncoder();
  const dataBuffer = encoder.encode(data);
  const signature = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', cryptoKey, dataBuffer);

  return base64UrlEncode(String.fromCharCode(...new Uint8Array(signature)));
}
