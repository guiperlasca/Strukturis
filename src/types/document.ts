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
}

export interface ProcessedDocument {
  originalFile: File;
  pages: PageResult[];
  overallConfidence: number;
  totalPages: number;
  processedAt: Date;
  documentType?: DocumentTypeInfo;
  detectedLanguage?: string;
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
