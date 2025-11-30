import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { 
  Upload, 
  FileText, 
  Trash2, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  ArrowLeft,
  Database,
  Loader2
} from "lucide-react";

interface ISODocument {
  id: string;
  filename: string;
  title: string | null;
  uploaded_at: string;
  processed: boolean;
}

interface ChunkStats {
  document_id: string;
  count: number;
}

const Admin = () => {
  const [documents, setDocuments] = useState<ISODocument[]>([]);
  const [chunkStats, setChunkStats] = useState<Map<string, number>>(new Map());
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const { data: docs, error } = await supabase
        .from("iso_documents")
        .select("*")
        .order("uploaded_at", { ascending: false });

      if (error) throw error;
      setDocuments(docs || []);

      // Get chunk counts
      const { data: chunks, error: chunkError } = await supabase
        .from("iso_chunks")
        .select("document_id");

      if (!chunkError && chunks) {
        const counts = new Map<string, number>();
        chunks.forEach((chunk) => {
          const current = counts.get(chunk.document_id) || 0;
          counts.set(chunk.document_id, current + 1);
        });
        setChunkStats(counts);
      }
    } catch (error) {
      console.error("Error fetching documents:", error);
      toast.error("Erreur lors du chargement des documents");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf") && !file.name.toLowerCase().endsWith(".txt")) {
      toast.error("Seuls les fichiers PDF et TXT sont acceptés");
      return;
    }

    setIsUploading(true);
    try {
      // Upload to storage
      const filePath = `${Date.now()}_${file.name}`;
      const { error: uploadError } = await supabase.storage
        .from("iso-documents")
        .upload(filePath, file);

      if (uploadError) throw uploadError;

      // Create document record
      const { data: doc, error: docError } = await supabase
        .from("iso_documents")
        .insert({
          filename: file.name,
          title: file.name.replace(/\.[^/.]+$/, "").replace(/_/g, " ")
        })
        .select()
        .single();

      if (docError) throw docError;

      toast.success("Document uploadé avec succès");
      
      // Auto-process the document
      await processDocument(doc.id, filePath, file.name);
      
      fetchDocuments();
    } catch (error) {
      console.error("Upload error:", error);
      toast.error("Erreur lors de l'upload");
    } finally {
      setIsUploading(false);
      e.target.value = "";
    }
  };

  const processDocument = async (documentId: string, filePath: string, filename: string) => {
    setIsProcessing(documentId);
    try {
      const { data, error } = await supabase.functions.invoke("process-document", {
        body: { documentId, filePath, filename }
      });

      if (error) throw error;

      if (data?.error) {
        throw new Error(data.error);
      }

      toast.success(`Document traité: ${data.chunks_created} chunks créés`);
      fetchDocuments();
    } catch (error) {
      console.error("Process error:", error);
      toast.error(error instanceof Error ? error.message : "Erreur lors du traitement");
    } finally {
      setIsProcessing(null);
    }
  };

  const deleteDocument = async (doc: ISODocument) => {
    if (!confirm(`Supprimer "${doc.filename}" et tous ses chunks ?`)) return;

    try {
      // Delete chunks first
      await supabase
        .from("iso_chunks")
        .delete()
        .eq("document_id", doc.id);

      // Delete document record
      const { error } = await supabase
        .from("iso_documents")
        .delete()
        .eq("id", doc.id);

      if (error) throw error;

      toast.success("Document supprimé");
      fetchDocuments();
    } catch (error) {
      console.error("Delete error:", error);
      toast.error("Erreur lors de la suppression");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b bg-card/95 backdrop-blur">
        <div className="flex h-16 items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-5 w-5" />
              </Button>
            </Link>
            <div>
              <h1 className="text-lg font-semibold">Administration</h1>
              <p className="text-xs text-muted-foreground">Gestion des documents ISO</p>
            </div>
          </div>
        </div>
      </header>

      <main className="container max-w-4xl py-8 px-4">
        <div className="space-y-8">
          {/* Upload Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Charger un document ISO
              </CardTitle>
              <CardDescription>
                Uploadez un fichier PDF ou TXT. Le document sera automatiquement découpé en chunks avec métadonnées.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid w-full items-center gap-2">
                  <Label htmlFor="file">Fichier PDF ou TXT</Label>
                  <Input
                    id="file"
                    type="file"
                    accept=".pdf,.txt"
                    onChange={handleFileUpload}
                    disabled={isUploading}
                    className="cursor-pointer"
                  />
                </div>
                {isUploading && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Upload et traitement en cours...
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Documents List */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    Documents chargés
                  </CardTitle>
                  <CardDescription>
                    {documents.length} document(s) dans la base de données
                  </CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={fetchDocuments}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Actualiser
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Aucun document chargé</p>
                  <p className="text-sm">Uploadez votre premier document ISO ci-dessus</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <div className="space-y-3">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-secondary/30 transition-colors"
                      >
                        <div className="flex items-center gap-3 min-w-0 flex-1">
                          <FileText className="h-8 w-8 text-primary flex-shrink-0" />
                          <div className="min-w-0">
                            <p className="font-medium truncate">{doc.filename}</p>
                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                              <span>
                                {new Date(doc.uploaded_at).toLocaleDateString("fr-FR")}
                              </span>
                              <span className="flex items-center gap-1">
                                {doc.processed ? (
                                  <>
                                    <CheckCircle className="h-3 w-3 text-green-500" />
                                    {chunkStats.get(doc.id) || 0} chunks
                                  </>
                                ) : (
                                  <>
                                    <AlertCircle className="h-3 w-3 text-amber-500" />
                                    Non traité
                                  </>
                                )}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {isProcessing === doc.id && (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => deleteDocument(doc)}
                            className="text-destructive hover:text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>

          {/* Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>Comment ça marche ?</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <ol className="list-decimal list-inside space-y-2">
                <li><strong>Uploadez</strong> vos documents ISO (PDF ou TXT)</li>
                <li>Le système <strong>extrait le texte</strong> automatiquement</li>
                <li>Le contenu est <strong>découpé en chunks</strong> avec détection des sections ISO (ex: 8.2.3)</li>
                <li>Chaque chunk contient les <strong>métadonnées</strong>: section, sous-section, page estimée</li>
                <li>Le chatbot utilise ces chunks pour <strong>répondre avec sources</strong></li>
              </ol>
              <p className="mt-4">
                <strong>Note:</strong> Les PDF scannés (images) nécessitent un OCR externe. 
                Pour de meilleurs résultats, utilisez des PDF texte ou des fichiers TXT.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Admin;
