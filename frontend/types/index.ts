export type SourceType = "note" | "url";
export type IndexingStatus = "pending" | "indexed" | "failed";

export interface KnowledgeItem {
  id: string;
  title: string;
  source_type: SourceType;
  original_url?: string | null;
  created_at: string;
  indexing_status: IndexingStatus;
  error_message?: string | null;
  chunk_count: number;
  preview: string;
}

export interface KnowledgeItemListResponse {
  items: KnowledgeItem[];
  total: number;
}

export interface IngestNotePayload {
  source_type: "note";
  title: string;
  content: string;
}

export interface IngestUrlPayload {
  source_type: "url";
  url: string;
}

export type IngestPayload = IngestNotePayload | IngestUrlPayload;

export interface IngestResponse {
  id: string;
  title: string;
  source_type: string;
  original_url?: string | null;
  indexing_status: string;
  chunk_count: number;
  created_at: string;
  message: string;
}

export interface Citation {
  chunk_id: string;
  item_id: string;
  title: string;
  source_type: string;
  url?: string | null;
  snippet: string;
  similarity_score: number;
}

export interface QueryResponse {
  question: string;
  answer: string;
  citations: Citation[];
  has_sufficient_context: boolean;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  database_connected: boolean;
  embedding_model: string;
  embedding_dimension: number;
  chat_model: string;
  environment: string;
}
