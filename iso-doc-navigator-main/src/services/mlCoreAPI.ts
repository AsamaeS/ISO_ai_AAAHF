/**
 * ML Core API Client
 * 
 * This service handles all communication with the ML Core backend API
 * for document ingestion and question answering.
 */

const ML_API_URL = import.meta.env.VITE_ML_API_URL || 'http://localhost:8000';

export interface AskQuestionRequest {
  query: string;
  top_k?: number;
  max_tokens?: number;
  temperature?: number;
}

export interface Source {
  document: string;
  section: string;
  section_name: string;
  page: number;
  chunk_id: string;
  relevance_score: number;
}

export interface AskQuestionResponse {
  answer: string;
  sources: Source[];
  query: string;
  num_sources: number;
  timestamp: string;
}

export interface IngestDocumentRequest {
  pdf_path: string;
  document_name?: string;
  rebuild_index?: boolean;
}

export interface IngestDocumentResponse {
  status: string;
  document_name: string;
  chunks_created: number;
  sections_parsed: number;
  index_updated: boolean;
  message: string;
}

export interface SystemInfoResponse {
  status: string;
  version: string;
  model: string;
  index_size: number;
  index_directory: string;
  uptime_seconds: number;
}

class MLCoreAPIClient {
  private baseURL: string;

  constructor(baseURL: string = ML_API_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Ask a question to the RAG system
   */
  async askQuestion(request: AskQuestionRequest): Promise<AskQuestionResponse> {
    const response = await fetch(`${this.baseURL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: request.query,
        top_k: request.top_k || 5,
        max_tokens: request.max_tokens || 512,
        temperature: request.temperature || 0.7,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get answer');
    }

    return response.json();
  }

  /**
   * Ingest a PDF document
   */
  async ingestDocument(request: IngestDocumentRequest): Promise<IngestDocumentResponse> {
    const response = await fetch(`${this.baseURL}/ingest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to ingest document');
    }

    return response.json();
  }

  /**
   * Get system information and status
   */
  async getSystemInfo(): Promise<SystemInfoResponse> {
    const response = await fetch(`${this.baseURL}/info`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get system info');
    }

    return response.json();
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${this.baseURL}/health`);

    if (!response.ok) {
      throw new Error('API health check failed');
    }

    return response.json();
  }
}

// Export singleton instance
export const mlCoreAPI = new MLCoreAPIClient();

// Export class for custom instances
export default MLCoreAPIClient;
