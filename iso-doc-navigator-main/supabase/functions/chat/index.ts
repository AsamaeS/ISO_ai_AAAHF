import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface ChatRequest {
  question: string;
  conversationId?: string;
}

interface ISOChunk {
  id: string;
  content: string;
  section: string | null;
  subsection: string | null;
  page_number: number | null;
  chunk_index: number;
  iso_documents: {
    filename: string;
    title: string | null;
  };
}

interface Source {
  document: string;
  section: string;
  subsection: string;
  chunk_id: number;
  page: number | null;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { question, conversationId } = (await req.json()) as ChatRequest;
    
    if (!question) {
      return new Response(
        JSON.stringify({ error: "Question is required" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const LOVABLE_API_KEY = Deno.env.get("LOVABLE_API_KEY");
    const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

    if (!LOVABLE_API_KEY) {
      throw new Error("LOVABLE_API_KEY is not configured");
    }

    // Create Supabase client
    const supabase = createClient(SUPABASE_URL!, SUPABASE_SERVICE_ROLE_KEY!);

    // Search for relevant chunks using full-text search
    const searchTerms = question
      .toLowerCase()
      .split(/\s+/)
      .filter(term => term.length > 2)
      .join(" & ");

    const { data: chunks, error: searchError } = await supabase
      .from("iso_chunks")
      .select(`
        id,
        content,
        section,
        subsection,
        page_number,
        chunk_index,
        iso_documents (
          filename,
          title
        )
      `)
      .textSearch("content", searchTerms, { type: "websearch", config: "french" })
      .limit(5);

    // If no results with full-text search, try simple ILIKE
    let relevantChunks: ISOChunk[] = [];
    
    if (!searchError && chunks && chunks.length > 0) {
      relevantChunks = chunks as unknown as ISOChunk[];
    } else {
      // Fallback to ILIKE search
      const keywords = question.split(/\s+/).filter(w => w.length > 3).slice(0, 3);
      if (keywords.length > 0) {
        const { data: fallbackChunks } = await supabase
          .from("iso_chunks")
          .select(`
            id,
            content,
            section,
            subsection,
            page_number,
            chunk_index,
            iso_documents (
              filename,
              title
            )
          `)
          .or(keywords.map(k => `content.ilike.%${k}%`).join(","))
          .limit(5);
        
        if (fallbackChunks) {
          relevantChunks = fallbackChunks as unknown as ISOChunk[];
        }
      }
    }

    // Build context from chunks
    let context = "";
    const sources: Source[] = [];

    if (relevantChunks.length > 0) {
      context = "Contexte ISO pertinent:\n\n";
      relevantChunks.forEach((chunk, index) => {
        const doc = chunk.iso_documents;
        context += `[Source ${index + 1}] Document: ${doc?.filename || "Unknown"}, Section: ${chunk.section || "N/A"}, Sous-section: ${chunk.subsection || "N/A"}\n`;
        context += `${chunk.content}\n\n`;
        
        sources.push({
          document: doc?.filename || "Document inconnu",
          section: chunk.section || "N/A",
          subsection: chunk.subsection || "N/A",
          chunk_id: chunk.chunk_index,
          page: chunk.page_number
        });
      });
    }

    // Build the prompt
    const systemPrompt = `Tu es un assistant expert en conformité ISO, spécialisé dans la norme ISO 9001:2015 et autres normes de management de la qualité.

RÈGLES STRICTES:
1. Tu DOIS répondre UNIQUEMENT en utilisant les informations fournies dans le contexte ISO ci-dessous.
2. Si l'information n'est PAS dans le contexte, réponds: "Information non trouvée dans la norme ISO disponible."
3. Chaque réponse DOIT être précise et citer les sources.
4. Réponds en français.
5. Sois concis mais complet.

${context || "AUCUN DOCUMENT ISO N'A ÉTÉ TROUVÉ DANS LA BASE DE DONNÉES. Informe l'utilisateur qu'il doit d'abord charger des documents ISO."}`;

    // Call Lovable AI
    const response = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${LOVABLE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-2.5-flash",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: question }
        ],
        stream: false,
      }),
    });

    if (!response.ok) {
      if (response.status === 429) {
        return new Response(
          JSON.stringify({ error: "Limite de requêtes atteinte. Veuillez réessayer plus tard." }),
          { status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
      if (response.status === 402) {
        return new Response(
          JSON.stringify({ error: "Crédits insuffisants. Veuillez recharger votre compte." }),
          { status: 402, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
      const errorText = await response.text();
      console.error("AI Gateway error:", response.status, errorText);
      throw new Error("Erreur du service IA");
    }

    const aiResponse = await response.json();
    const answer = aiResponse.choices?.[0]?.message?.content || "Impossible de générer une réponse.";

    // Save message to database if conversationId provided
    if (conversationId) {
      await supabase.from("chat_messages").insert([
        { conversation_id: conversationId, role: "user", content: question },
        { conversation_id: conversationId, role: "assistant", content: answer, sources: sources.length > 0 ? sources : null }
      ]);
    }

    return new Response(
      JSON.stringify({ 
        answer, 
        sources: sources.length > 0 ? sources : null 
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (error) {
    console.error("Chat error:", error);
    return new Response(
      JSON.stringify({ error: error instanceof Error ? error.message : "Une erreur est survenue" }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
