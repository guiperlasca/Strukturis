-- Criar novas tabelas para Document AI
CREATE TABLE IF NOT EXISTS public.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  original_url TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  total_pages INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'processing'
);

CREATE TABLE IF NOT EXISTS public.document_pages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
  page INTEGER NOT NULL,
  status TEXT NOT NULL,
  confidence NUMERIC(5,2),
  quality_hints JSONB,
  text TEXT,
  tables JSONB,
  entities JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.document_exports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
  json_url TEXT,
  csv_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_exports ENABLE ROW LEVEL SECURITY;

-- RLS policies for documents
CREATE POLICY "Users can view their own documents"
  ON public.documents FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own documents"
  ON public.documents FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own documents"
  ON public.documents FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own documents"
  ON public.documents FOR DELETE
  USING (auth.uid() = user_id);

-- RLS policies for document_pages
CREATE POLICY "Users can view pages of their own documents"
  ON public.document_pages FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.documents
    WHERE documents.id = document_pages.document_id
    AND documents.user_id = auth.uid()
  ));

CREATE POLICY "Users can insert pages for their own documents"
  ON public.document_pages FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM public.documents
    WHERE documents.id = document_pages.document_id
    AND documents.user_id = auth.uid()
  ));

-- RLS policies for document_exports
CREATE POLICY "Users can view exports of their own documents"
  ON public.document_exports FOR SELECT
  USING (EXISTS (
    SELECT 1 FROM public.documents
    WHERE documents.id = document_exports.document_id
    AND documents.user_id = auth.uid()
  ));

CREATE POLICY "Users can insert exports for their own documents"
  ON public.document_exports FOR INSERT
  WITH CHECK (EXISTS (
    SELECT 1 FROM public.documents
    WHERE documents.id = document_exports.document_id
    AND documents.user_id = auth.uid()
  ));

-- Create indexes
CREATE INDEX idx_documents_user_id ON public.documents(user_id);
CREATE INDEX idx_document_pages_document_id ON public.document_pages(document_id);
CREATE INDEX idx_document_exports_document_id ON public.document_exports(document_id);