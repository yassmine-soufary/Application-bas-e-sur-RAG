export interface Source { id: number; chunk_id: string; file: string; reference: string; date: string; page: number; section: string; excerpt: string; score: number }
export interface Answer { answer: string; found: boolean; sources: Source[]; invalid_citations: number[]; latency_ms: number }
export interface DocumentInfo { file: string; reference: string; type: string; date: string; version: string; status: string; chunks: number }
export interface Chunk extends Omit<DocumentInfo, 'chunks'> { id: string; page: number; section: string; text: string }
export interface SearchHit { chunk: Chunk; score: number }
export interface SearchResponse { hits: SearchHit[] }
export interface Health { server: string; chroma: string; chunks: number; openai_configured: boolean }
export interface IngestResult { collection: string; chunks: number; reused: boolean }
export interface Query { question: string; top_k: number; filters: { type: string | null } }
export class ApiError extends Error { constructor(public status: number, message: string) { super(message); } }
const base = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
async function request<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try { response = await fetch(`${base}/api/${path}`, { method: body === undefined ? 'GET' : 'POST', headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(180000) }); }
  catch { throw new ApiError(0, 'Connexion impossible. Vérifiez que le backend est démarré.'); }
  const data = await response.json();
  if (!response.ok) { const label = response.status === 422 ? 'Entrée invalide' : response.status === 502 ? 'OpenAI indisponible' : response.status === 503 ? 'Base documentaire indisponible' : 'Erreur serveur'; throw new ApiError(response.status, `${label} : ${typeof data.detail === 'string' ? data.detail : 'Vérifiez les paramètres saisis.'}`); }
  return data as T;
}
export const api = { health: () => request<Health>('health'), documents: () => request<DocumentInfo[]>('documents'), ask: (q: Query) => request<Answer>('ask', q), search: (q: Query) => request<SearchResponse>('search', q), ingest: (strategy: string, chunk_size: number, overlap: number) => request<IngestResult>('ingest', { strategy, chunk_size, overlap }) };
