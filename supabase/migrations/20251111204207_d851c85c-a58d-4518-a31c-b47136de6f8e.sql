-- Fix function search_path for security with CASCADE
DROP FUNCTION IF EXISTS public.update_document_completed_at() CASCADE;

CREATE OR REPLACE FUNCTION public.update_document_completed_at()
RETURNS TRIGGER 
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.status IN ('completed', 'failed', 'partial') AND OLD.status = 'processing' THEN
    NEW.completed_at = now();
  END IF;
  RETURN NEW;
END;
$$;

-- Recreate the trigger
CREATE TRIGGER update_ocr_documents_completed_at
BEFORE UPDATE ON public.ocr_documents
FOR EACH ROW
EXECUTE FUNCTION public.update_document_completed_at();