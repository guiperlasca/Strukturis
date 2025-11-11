export interface TextSegment {
  text: string;
  confidence: number;
  startIndex: number;
  endIndex: number;
}

export interface PageResult {
  pageNumber: number;
  text: string;
  segments: TextSegment[];
  confidence: number;
  hasTable: boolean;
  tableData?: string[][];
  language?: string;
  status?: 'ok' | 'low_quality' | 'error';
  qualityHints?: string[];
  tables?: Array<{
    name: string;
    confidence: number;
    rows: string[][];
  }>;
  entities?: Array<{
    field: string;
    value: string;
    confidence: number;
  }>;
}

export interface ProcessedDocument {
  originalFile: File;
  pages: PageResult[];
  overallConfidence: number;
  totalPages: number;
  processedAt: Date;
  processingTime: number; // in milliseconds
  documentType?: DocumentTypeInfo;
  detectedLanguage?: string;
  summary?: {
    readabilityConfidence: number;
    pageSuccessRate: number;
    tablesDetected: number;
    fieldsDetected: number;
  };
  exports?: {
    jsonUrl?: string;
    csvUrl?: string;
  };
}

export type ProcessStep = 
  | "upload"
  | "preprocessing" 
  | "ocr"
  | "extraction"
  | "review"
  | "export";

export type DocumentType = 
  | "legal_petition"
  | "contract"
  | "invoice"
  | "resume"
  | "id_document"
  | "receipt"
  | "report"
  | "letter"
  | "form"
  | "payslip"
  | "personnel_file"
  | "timecard"
  | "other";

export interface DocumentTypeInfo {
  type: DocumentType;
  confidence: number;
  label: string;
  icon: string;
}
