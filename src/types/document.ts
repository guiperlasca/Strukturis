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
}

export interface ProcessedDocument {
  originalFile: File;
  pages: PageResult[];
  overallConfidence: number;
  totalPages: number;
  processedAt: Date;
}

export type ProcessStep = 
  | "upload"
  | "preprocessing" 
  | "ocr"
  | "extraction"
  | "review"
  | "export";
