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

// Configuration helper with validation
function getDocAIConfig() {
  const credentialsJson = Deno.env.get('GOOGLE_APPLICATION_CREDENTIALS_JSON');
  const projectId = Deno.env.get('DOCAI_PROJECT_ID')?.trim();
  const location = Deno.env.get('DOCAI_LOCATION')?.trim() || 'us';
  const processorId = Deno.env.get('DOCAI_PROCESSOR_ID')?.trim();

  console.log('Document AI Configuration Check:', {
    hasCredentials: !!credentialsJson,
    credentialsLength: credentialsJson?.length,
    projectId: projectId || 'MISSING',
    location,
    processorId: processorId || 'MISSING',
    processorIdLength: processorId?.length,
  });

  // Validate configuration
  const errors: string[] = [];
  
  if (!credentialsJson) {
    errors.push('GOOGLE_APPLICATION_CREDENTIALS_JSON is not set');
  } else {
    try {
      JSON.parse(credentialsJson);
    } catch {
      errors.push('GOOGLE_APPLICATION_CREDENTIALS_JSON is not valid JSON');
    }
  }

  if (!projectId) {
    errors.push('DOCAI_PROJECT_ID is not set');
  } else if (!/^[a-z0-9-]+$/.test(projectId)) {
    errors.push('DOCAI_PROJECT_ID has invalid format (should be lowercase alphanumeric with hyphens)');
  }

  if (!processorId) {
    errors.push('DOCAI_PROCESSOR_ID is not set');
  } else if (!/^[a-f0-9]+$/.test(processorId)) {
    errors.push('DOCAI_PROCESSOR_ID has invalid format (should be hexadecimal)');
  }

  if (errors.length > 0) {
    console.error('Configuration errors:', errors);
    return { valid: false, errors };
  }

  return {
    valid: true,
    credentials: JSON.parse(credentialsJson!),
    projectId: projectId!,
    location,
    processorId: processorId!,
  };
}

// Retry helper for transient failures
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  let lastError: Error | null = null;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      console.log(`Attempt ${i + 1} failed:`, error);
      
      if (i < maxRetries - 1) {
        const delay = baseDelay * Math.pow(2, i);
        console.log(`Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError;
}

// Optimized base64 encoding for large files
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  const chunkSize = 8192;
  const chunks: string[] = [];
  
  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.slice(i, i + chunkSize);
    chunks.push(String.fromCharCode(...chunk));
  }
  
  return btoa(chunks.join(''));
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log('=== Process Document Request Started ===');
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    if (!supabaseUrl || !supabaseKey) {
      throw new Error('Supabase configuration missing');
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    // Authenticate user
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      return new Response(
        JSON.stringify({ error: 'Authorization header required' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const token = authHeader.replace('Bearer ', '');
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);

    if (authError || !user) {
      console.error('Authentication failed:', authError);
      return new Response(
        JSON.stringify({ error: 'Invalid or expired token' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    console.log('User authenticated:', user.id);

    // Parse and validate request body
    const body: ProcessRequest = await req.json();
    const { fileUrl, mimeType, pagesMode, pagesCount, pagesList, export: exportOptions } = body;

    console.log('Request details:', { 
      fileUrl: fileUrl?.substring(0, 50) + '...', 
      mimeType, 
      pagesMode,
      pagesCount,
      pagesList: pagesList?.length,
    });

    if (!fileUrl || !mimeType || !pagesMode) {
      return new Response(
        JSON.stringify({ 
          error: 'Missing required fields',
          required: ['fileUrl', 'mimeType', 'pagesMode'],
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Validate and get Document AI configuration
    const config = getDocAIConfig();
    if (!config.valid) {
      return new Response(
        JSON.stringify({ 
          error: 'Document AI configuration error',
          details: config.errors,
          help: 'Please check your environment variables in Supabase dashboard',
        }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const { credentials, projectId, location, processorId } = config;

    // Download file from storage
    console.log('Downloading file from storage...');
    const filePath = fileUrl.replace(/^.*\/documents\//, '');
    
    const { data: fileData, error: downloadError } = await supabase.storage
      .from('documents')
      .download(filePath);

    if (downloadError || !fileData) {
      console.error('File download error:', downloadError);
      return new Response(
        JSON.stringify({ 
          error: 'Failed to download file',
          details: downloadError?.message,
          filePath,
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    const fileSize = fileData.size;
    const MAX_SIZE = 20 * 1024 * 1024; // 20MB Document AI limit

    console.log(`File downloaded: ${(fileSize / 1024 / 1024).toFixed(2)}MB`);

    if (fileSize > MAX_SIZE) {
      return new Response(
        JSON.stringify({ 
          error: 'File too large',
          size: `${(fileSize / 1024 / 1024).toFixed(2)}MB`,
          limit: '20MB',
        }),
        { status: 413, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    // Convert file to base64
    console.log('Converting file to base64...');
    const arrayBuffer = await fileData.arrayBuffer();
    const base64Content = arrayBufferToBase64(arrayBuffer);
    console.log('Base64 conversion complete');

    // Get OAuth token with retry
    console.log('Getting OAuth token...');
    const tokenResponse = await retryWithBackoff(async () => {
      const jwt = await createJWT(credentials);
      
      const response = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
          assertion: jwt,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('OAuth error response:', errorText);
        throw new Error(`OAuth failed: ${errorText}`);
      }

      return response.json();
    });

    const { access_token } = tokenResponse;
    console.log('OAuth token obtained successfully');

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
      throw new Error('Failed to create document record');
    }

    const documentId = docData.id;
    console.log('Document record created:', documentId);

    // Call Document AI with retry
    const processorEndpoint = `https://${location}-documentai.googleapis.com/v1/projects/${projectId}/locations/${location}/processors/${processorId}:process`;

    console.log('Calling Document AI:', {
      endpoint: processorEndpoint,
      mimeType,
      fileSize: `${(fileSize / 1024).toFixed(2)}KB`,
    });

    const docAIResult = await retryWithBackoff(async () => {
      const response = await fetch(processorEndpoint, {
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

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Document AI error:', {
          status: response.status,
          statusText: response.statusText,
          body: errorText,
        });
        
        // Update document status
        await supabase
          .from('documents')
          .update({ status: 'failed' })
          .eq('id', documentId);

        throw new Error(`Document AI failed (${response.status}): ${errorText}`);
      }

      return response.json();
    }, 2, 2000); // 2 retries with 2s base delay

    console.log('Document AI processing successful');
    const document = docAIResult.document;

    if (!document || !document.pages) {
      throw new Error('Document AI returned invalid response structure');
    }

    // Determine pages to process
    const totalPages = document.pages.length;
    let pagesToProcess: number[] = [];

    if (pagesMode === 'all') {
      pagesToProcess = Array.from({ length: totalPages }, (_, i) => i + 1);
    } else if (pagesMode === 'count' && pagesCount) {
      pagesToProcess = Array.from({ length: Math.min(pagesCount, totalPages) }, (_, i) => i + 1);
    } else if (pagesMode === 'custom' && pagesList) {
      pagesToProcess = pagesList.filter(p => p >= 1 && p <= totalPages);
    }

    console.log(`Processing ${pagesToProcess.length} of ${totalPages} pages`);

    // Process each page
    const pageResults: PageResult[] = [];
    let totalConfidence = 0;
    let successCount = 0;

    for (const pageNum of pagesToProcess) {
      const pageIndex = pageNum - 1;
      const page = document.pages[pageIndex];

      if (!page) {
        console.warn(`Page ${pageNum} not found, skipping`);
        continue;
      }

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
      const tables = extractTables(document, page, pageIndex);

      // Extract entities
      const entities = extractEntities(document, pageIndex);

      const pageResult: PageResult = {
        page: pageNum,
        status,
        qualityHints,
        text: pageText,
        tables,
        entities,
        confidence: Math.round(confidence),
      };

      pageResults.push(pageResult);

      // Save to database
      await supabase.from('document_pages').insert({
        document_id: documentId,
        page: pageNum,
        status,
        confidence: Math.round(confidence),
        quality_hints: qualityHints,
        text: pageText,
        tables: tables,
        entities: entities,
      });

      console.log(`Page ${pageNum} processed: ${status}, confidence: ${Math.round(confidence)}%`);
    }

    // Calculate metrics
    const readabilityConfidence = pagesToProcess.length > 0 
      ? Math.round(totalConfidence / pagesToProcess.length)
      : 0;
    const pageSuccessRate = pagesToProcess.length > 0 
      ? Math.round((successCount / pagesToProcess.length) * 100)
      : 0;
    const tablesDetected = pageResults.reduce((sum, p) => sum + p.tables.length, 0);
    const fieldsDetected = pageResults.reduce((sum, p) => sum + p.entities.length, 0);

    console.log('Processing summary:', {
      readabilityConfidence,
      pageSuccessRate,
      tablesDetected,
      fieldsDetected,
    });

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
      const jsonData = JSON.stringify({
        documentId,
        pageResults,
        summary: {
          readabilityConfidence,
          pageSuccessRate,
          tablesDetected,
          fieldsDetected,
        },
      }, null, 2);
      
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

    console.log('=== Process Document Request Completed Successfully ===');

    return new Response(
      JSON.stringify({
        documentId,
        pagesProcessed: pagesToProcess,
        summary: {
          readabilityConfidence,
          pageSuccessRate,
          tablesDetected,
          fieldsDetected,
        },
        pages: pageResults,
        exports,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );

  } catch (error) {
    console.error('=== Process Document Request Failed ===');
    console.error('Error:', error);
    
    return new Response(
      JSON.stringify({ 
        error: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

// Helper functions
function extractPageText(document: any, page: any): string {
  const getText = (segment: any) => {
    if (!segment?.layout?.textAnchor?.textSegments) return '';
    
    return segment.layout.textAnchor.textSegments
      .map((s: any) => {
        const start = parseInt(s.startIndex || '0');
        const end = parseInt(s.endIndex || '0');
        return document.text?.substring(start, end) || '';
      })
      .join('');
  };

  const texts: string[] = [];

  if (page.paragraphs) {
    texts.push(...page.paragraphs.map(getText));
  } else if (page.lines) {
    texts.push(...page.lines.map(getText));
  } else if (page.tokens) {
    texts.push(...page.tokens.map(getText));
  }

  return texts.filter(t => t.trim()).join('\n');
}

function calculatePageConfidence(page: any): number {
  const scores: number[] = [];

  // Language detection confidence
  if (page.detectedLanguages?.[0]?.confidence) {
    scores.push(page.detectedLanguages[0].confidence * 100);
  }

  // Quality score
  if (page.quality?.qualityScore) {
    scores.push(page.quality.qualityScore * 100);
  }

  // Default confidence if no scores available
  if (scores.length === 0) {
    return 75;
  }

  // Average of available scores
  return scores.reduce((sum, score) => sum + score, 0) / scores.length;
}

function detectQualityIssues(page: any): string[] {
  const hints: string[] = [];
  
  // Check for page skew
  if (page.transforms) {
    for (const transform of page.transforms) {
      if (Math.abs(transform.rows?.[0]?.[1] || 0) > 0.1) {
        hints.push('skew');
        break;
      }
    }
  }
  
  // Check quality score
  const qualityScore = page.quality?.qualityScore || 1;
  
  if (qualityScore < 0.5) {
    hints.push('blur');
  }
  if (qualityScore < 0.3) {
    hints.push('shadow');
  }
  
  // Check for defects
  if (page.quality?.defects) {
    for (const defect of page.quality.defects) {
      if (defect.type && !hints.includes(defect.type)) {
        hints.push(defect.type);
      }
    }
  }
  
  return [...new Set(hints)]; // Remove duplicates
}

function extractTables(document: any, page: any, pageIndex: number): TableData[] {
  if (!page.tables || page.tables.length === 0) return [];
  
  return page.tables.map((table: any, idx: number) => {
    const rows: string[][] = [];
    
    const extractCellText = (cell: any): string => {
      if (!cell?.layout?.textAnchor?.textSegments) return '';
      
      return cell.layout.textAnchor.textSegments
        .map((segment: any) => {
          const start = parseInt(segment.startIndex || '0');
          const end = parseInt(segment.endIndex || '0');
          return document.text?.substring(start, end) || '';
        })
        .join('')
        .trim();
    };
    
    // Extract header rows
    if (table.headerRows) {
      for (const row of table.headerRows) {
        const cells = (row.cells || []).map(extractCellText);
        if (cells.some(c => c)) rows.push(cells);
      }
    }
    
    // Extract body rows
    if (table.bodyRows) {
      for (const row of table.bodyRows) {
        const cells = (row.cells || []).map(extractCellText);
        if (cells.some(c => c)) rows.push(cells);
      }
    }
    
    return {
      name: `table_${pageIndex + 1}_${idx + 1}`,
      confidence: table.detectionConfidence ? Math.round(table.detectionConfidence * 100) : 85,
      rows,
    };
  }).filter(table => table.rows.length > 0);
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
      confidence: entity.confidence ? Math.round(entity.confidence * 100) : 0,
    }))
    .filter((e: Entity) => e.value.trim() !== '');
}

function generateCSV(pageResults: PageResult[]): string {
  const allRows: string[][] = [['Page', 'Table', 'Row', ...Array.from({ length: 20 }, (_, i) => `Col${i + 1}`)]];
  
  for (const page of pageResults) {
    for (const table of page.tables) {
      for (let rowIdx = 0; rowIdx < table.rows.length; rowIdx++) {
        const row = table.rows[rowIdx];
        const csvRow = [
          page.page.toString(),
          table.name,
          (rowIdx + 1).toString(),
          ...row.map(cell => `"${cell.replace(/"/g, '""')}"`),
        ];
        allRows.push(csvRow);
      }
    }
  }
  
  return allRows.map(row => row.join(',')).join('\n');
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
  // Clean up the private key
  const cleanKey = privateKey.replace(/\\n/g, '\n');
  
  const pemHeader = '-----BEGIN PRIVATE KEY-----';
  const pemFooter = '-----END PRIVATE KEY-----';
  
  // Extract base64 content
  const pemContents = cleanKey
    .replace(pemHeader, '')
    .replace(pemFooter, '')
    .replace(/\s/g, '');

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