-- Create storage bucket for ISO documents
INSERT INTO storage.buckets (id, name, public) VALUES ('iso-documents', 'iso-documents', false);

-- Allow anyone to upload to the bucket (for demo, add auth later)
CREATE POLICY "Anyone can upload ISO documents"
ON storage.objects FOR INSERT
WITH CHECK (bucket_id = 'iso-documents');

CREATE POLICY "Anyone can read ISO documents"
ON storage.objects FOR SELECT
USING (bucket_id = 'iso-documents');

CREATE POLICY "Anyone can delete ISO documents"
ON storage.objects FOR DELETE
USING (bucket_id = 'iso-documents');

-- Add policies to allow inserting ISO documents and chunks
CREATE POLICY "Anyone can insert ISO documents"
ON public.iso_documents FOR INSERT
WITH CHECK (true);

CREATE POLICY "Anyone can update ISO documents"
ON public.iso_documents FOR UPDATE
USING (true);

CREATE POLICY "Anyone can insert ISO chunks"
ON public.iso_chunks FOR INSERT
WITH CHECK (true);

CREATE POLICY "Anyone can delete ISO chunks"
ON public.iso_chunks FOR DELETE
USING (true);