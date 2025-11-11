-- Update the documents bucket to allow larger files (100MB)
UPDATE storage.buckets 
SET file_size_limit = 104857600  -- 100MB in bytes
WHERE id = 'documents';
