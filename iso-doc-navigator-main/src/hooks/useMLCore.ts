/**
 * React hook for ML Core API
 * 
 * Provides easy-to-use hooks for interacting with the ML backend
 */

import { useMutation, useQuery } from '@tanstack/react-query';
import { mlCoreAPI, type AskQuestionRequest, type IngestDocumentRequest } from '@/services/mlCoreAPI';
import { toast } from 'sonner';

/**
 * Hook to ask questions to the RAG system
 */
export function useAskQuestion() {
    return useMutation({
        mutationFn: (request: AskQuestionRequest) => mlCoreAPI.askQuestion(request),
        onError: (error: Error) => {
            toast.error('Failed to get answer', {
                description: error.message,
            });
        },
    });
}

/**
 * Hook to ingest PDF documents
 */
export function useIngestDocument() {
    return useMutation({
        mutationFn: (request: IngestDocumentRequest) => mlCoreAPI.ingestDocument(request),
        onSuccess: (data) => {
            toast.success('Document ingested successfully', {
                description: `${data.chunks_created} chunks created from ${data.document_name}`,
            });
        },
        onError: (error: Error) => {
            toast.error('Failed to ingest document', {
                description: error.message,
            });
        },
    });
}

/**
 * Hook to get system information
 */
export function useSystemInfo() {
    return useQuery({
        queryKey: ['ml-system-info'],
        queryFn: () => mlCoreAPI.getSystemInfo(),
        refetchInterval: 30000, // Refetch every 30 seconds
    });
}

/**
 * Hook for API health check
 */
export function useHealthCheck() {
    return useQuery({
        queryKey: ['ml-health'],
        queryFn: () => mlCoreAPI.healthCheck(),
        refetchInterval: 10000, // Check every 10 seconds
        retry: 3,
    });
}
