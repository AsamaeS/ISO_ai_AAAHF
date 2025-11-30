import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface ProcessRequest {
  documentId: string;
  filePath: string;
  filename: string;
}

// Simple text extraction - extracts readable text from PDF binary
function extractTextFromPDF(pdfBuffer: ArrayBuffer): string {
  const bytes = new Uint8Array(pdfBuffer);
  const text = new TextDecoder("utf-8", { fatal: false }).decode(bytes);
  
  // Extract text between stream and endstream markers (PDF text streams)
  const textParts: string[] = [];
  
  // Look for text in parentheses (PDF string literals)
  const parenRegex = /\(([^)]+)\)/g;
  let match;
  while ((match = parenRegex.exec(text)) !== null) {
    const content = match[1]
      .replace(/\\n/g, "\n")
      .replace(/\\r/g, "\r")
      .replace(/\\t/g, "\t")
      .replace(/\\\(/g, "(")
      .replace(/\\\)/g, ")")
      .replace(/\\\\/g, "\\");
    if (content.length > 2 && /[a-zA-Z0-9àâäéèêëïîôùûüç]/.test(content)) {
      textParts.push(content);
    }
  }
  
  // Also try to extract text from BT/ET blocks (text objects)
  const btEtRegex = /BT\s*([\s\S]*?)\s*ET/g;
  while ((match = btEtRegex.exec(text)) !== null) {
    const block = match[1];
    // Extract Tj and TJ operators
    const tjRegex = /\(([^)]+)\)\s*Tj/g;
    let tjMatch;
    while ((tjMatch = tjRegex.exec(block)) !== null) {
      const tjContent = tjMatch[1];
      if (tjContent.length > 1) {
        textParts.push(tjContent);
      }
    }
  }
  
  return textParts.join(" ").replace(/\s+/g, " ").trim();
}

// Extract sections from ISO document text
function extractSections(text: string): { section: string; subsection: string; content: string; page: number }[] {
  const sections: { section: string; subsection: string; content: string; page: number }[] = [];
  
  // Pattern for ISO sections like "4.1", "8.2.3", etc.
  const sectionPattern = /(\d+(?:\.\d+)*)\s+([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ][^.!?\n]+)/g;
  
  let currentSection = "1";
  let currentSubsection = "";
  let currentContent = "";
  let estimatedPage = 1;
  
  const lines = text.split(/\n|(?<=\.)\s+(?=[A-Z])/);
  let charCount = 0;
  
  for (const line of lines) {
    charCount += line.length;
    // Estimate page (roughly 3000 chars per page)
    estimatedPage = Math.ceil(charCount / 3000);
    
    const sectionMatch = line.match(/^(\d+(?:\.\d+)*)\s+/);
    
    if (sectionMatch) {
      // Save previous section
      if (currentContent.trim()) {
        sections.push({
          section: currentSection,
          subsection: currentSubsection,
          content: currentContent.trim(),
          page: estimatedPage
        });
      }
      
      const parts = sectionMatch[1].split(".");
      currentSection = parts[0];
      currentSubsection = sectionMatch[1];
      currentContent = line;
    } else {
      currentContent += " " + line;
    }
  }
  
  // Add last section
  if (currentContent.trim()) {
    sections.push({
      section: currentSection,
      subsection: currentSubsection,
      content: currentContent.trim(),
      page: estimatedPage
    });
  }
  
  return sections;
}

// Chunk text into smaller pieces
function chunkText(text: string, maxChunkSize: number = 1500): string[] {
  const chunks: string[] = [];
  const sentences = text.split(/(?<=[.!?])\s+/);
  let currentChunk = "";
  
  for (const sentence of sentences) {
    if (currentChunk.length + sentence.length > maxChunkSize && currentChunk) {
      chunks.push(currentChunk.trim());
      currentChunk = sentence;
    } else {
      currentChunk += (currentChunk ? " " : "") + sentence;
    }
  }
  
  if (currentChunk.trim()) {
    chunks.push(currentChunk.trim());
  }
  
  return chunks;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { documentId, filePath, filename } = (await req.json()) as ProcessRequest;
    
    console.log(`Processing document: ${filename}, path: ${filePath}`);

    const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
    
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    // Download the file from storage
    const { data: fileData, error: downloadError } = await supabase.storage
      .from("iso-documents")
      .download(filePath);

    if (downloadError || !fileData) {
      console.error("Download error:", downloadError);
      throw new Error(`Failed to download file: ${downloadError?.message}`);
    }

    console.log(`File downloaded, size: ${fileData.size} bytes`);

    // Extract text from PDF
    const buffer = await fileData.arrayBuffer();
    let extractedText = extractTextFromPDF(buffer);
    
    // If PDF extraction fails, try raw text
    if (extractedText.length < 100) {
      extractedText = await fileData.text();
    }
    
    console.log(`Extracted text length: ${extractedText.length}`);

    if (extractedText.length < 50) {
      throw new Error("Could not extract meaningful text from the document. The PDF might be image-based and require OCR.");
    }

    // Extract sections
    const sections = extractSections(extractedText);
    console.log(`Found ${sections.length} sections`);

    // Create chunks with metadata
    const allChunks: {
      document_id: string;
      chunk_index: number;
      content: string;
      section: string;
      subsection: string;
      page_number: number;
    }[] = [];

    let chunkIndex = 0;

    if (sections.length > 0) {
      for (const section of sections) {
        const sectionChunks = chunkText(section.content);
        for (const chunkContent of sectionChunks) {
          allChunks.push({
            document_id: documentId,
            chunk_index: chunkIndex++,
            content: chunkContent,
            section: section.section,
            subsection: section.subsection,
            page_number: section.page
          });
        }
      }
    } else {
      // Fallback: chunk entire text
      const chunks = chunkText(extractedText);
      let page = 1;
      for (const chunkContent of chunks) {
        allChunks.push({
          document_id: documentId,
          chunk_index: chunkIndex++,
          content: chunkContent,
          section: "1",
          subsection: "",
          page_number: page++
        });
      }
    }

    console.log(`Created ${allChunks.length} chunks`);

    // Delete existing chunks for this document
    await supabase
      .from("iso_chunks")
      .delete()
      .eq("document_id", documentId);

    // Insert chunks in batches
    const batchSize = 50;
    for (let i = 0; i < allChunks.length; i += batchSize) {
      const batch = allChunks.slice(i, i + batchSize);
      const { error: insertError } = await supabase
        .from("iso_chunks")
        .insert(batch);
      
      if (insertError) {
        console.error("Insert error:", insertError);
        throw new Error(`Failed to insert chunks: ${insertError.message}`);
      }
    }

    // Update document as processed
    await supabase
      .from("iso_documents")
      .update({ processed: true })
      .eq("id", documentId);

    return new Response(
      JSON.stringify({ 
        success: true, 
        chunks_created: allChunks.length,
        text_length: extractedText.length,
        sections_found: sections.length
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (error) {
    console.error("Process error:", error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : "Processing failed" }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
