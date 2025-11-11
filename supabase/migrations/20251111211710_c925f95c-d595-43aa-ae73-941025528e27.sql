-- Update the documents bucket limit back to 10MB to match function constraints
UPDATE storage.buckets 
SET file_size_limit = 10485760  -- 10MB in bytes
WHERE id = 'documents';