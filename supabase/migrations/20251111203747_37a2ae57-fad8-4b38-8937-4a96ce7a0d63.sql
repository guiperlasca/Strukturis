-- Create storage bucket for document uploads
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'documents',
  'documents',
  false,
  20971520, -- 20MB limit
  ARRAY['application/pdf', 'image/jpeg', 'image/png', 'image/webp']
);

-- Create storage policies for document uploads
CREATE POLICY "Allow authenticated users to upload documents"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Allow users to read their own documents"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Allow users to delete their own documents"
ON storage.objects
FOR DELETE
TO authenticated
USING (bucket_id = 'documents' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Create OCR processing history table
CREATE TABLE public.ocr_documents (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID,
  original_filename TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  file_size BIGINT,
  mime_type TEXT,
  status TEXT NOT NULL DEFAULT 'processing',
  overall_confidence DECIMAL(5,2),
  total_pages INTEGER,
  processing_time_ms INTEGER,
  document_type TEXT,
  detected_language TEXT,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  completed_at TIMESTAMP WITH TIME ZONE,
  CONSTRAINT valid_status CHECK (status IN ('processing', 'completed', 'failed', 'partial'))
);

-- Create pages table for detailed page-level data
CREATE TABLE public.ocr_pages (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES public.ocr_documents(id) ON DELETE CASCADE,
  page_number INTEGER NOT NULL,
  raw_text TEXT,
  corrected_text TEXT,
  confidence DECIMAL(5,2),
  has_table BOOLEAN DEFAULT false,
  table_data JSONB,
  detected_language TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(document_id, page_number)
);

-- Enable Row Level Security
ALTER TABLE public.ocr_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ocr_pages ENABLE ROW LEVEL SECURITY;

-- RLS policies for ocr_documents
CREATE POLICY "Users can view their own documents"
ON public.ocr_documents
FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own documents"
ON public.ocr_documents
FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own documents"
ON public.ocr_documents
FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own documents"
ON public.ocr_documents
FOR DELETE
USING (auth.uid() = user_id);

-- RLS policies for ocr_pages
CREATE POLICY "Users can view pages of their own documents"
ON public.ocr_pages
FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM public.ocr_documents
    WHERE ocr_documents.id = ocr_pages.document_id
    AND ocr_documents.user_id = auth.uid()
  )
);

CREATE POLICY "Users can insert pages for their own documents"
ON public.ocr_pages
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.ocr_documents
    WHERE ocr_documents.id = ocr_pages.document_id
    AND ocr_documents.user_id = auth.uid()
  )
);

-- Create indexes for better performance
CREATE INDEX idx_ocr_documents_user_id ON public.ocr_documents(user_id);
CREATE INDEX idx_ocr_documents_status ON public.ocr_documents(status);
CREATE INDEX idx_ocr_documents_created_at ON public.ocr_documents(created_at DESC);
CREATE INDEX idx_ocr_pages_document_id ON public.ocr_pages(document_id);

-- Create function to update completed_at timestamp
CREATE OR REPLACE FUNCTION public.update_document_completed_at()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status IN ('completed', 'failed', 'partial') AND OLD.status = 'processing' THEN
    NEW.completed_at = now();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic timestamp updates
CREATE TRIGGER update_ocr_documents_completed_at
BEFORE UPDATE ON public.ocr_documents
FOR EACH ROW
EXECUTE FUNCTION public.update_document_completed_at();