import axios from "axios";

// Можно вынести в .env или config
// @ts-ignore
const BASE_URL = (window as any).REACT_APP_API_URL || "http://localhost:8000";

// ==================== MODELS ====================

export interface LLMModelConfig {
  name: string;
  type: string;
  model_path: string;
  params: Record<string, any>;
  temperature: number;
  top_p: number;
}

export interface GenerateRequest {
  model: string;
  prompt: string;
  params?: Record<string, any>;
  max_new_tokens?: number;
  temperature?: number;
  top_p?: number;
  user_id?: string;
}

export interface GenerateResponse {
  model: string;
  prompt: string;
  result: string;
  usage?: any;
  id?: string;
}

export interface SetModelParamRequest {
  model: string;
  param: string;
  value: any;
}

// ==================== API METHODS ====================

export async function getModelConfigs(): Promise<Record<string, LLMModelConfig>> {
  const res = await axios.get(`${BASE_URL}/admin/model_configs`);
  return res.data;
}

export async function setModelParam(req: SetModelParamRequest) {
  const res = await axios.post(`${BASE_URL}/admin/set_model_param`, req);
  return res.data;
}

export async function setDefaultModel(model: string) {
  const res = await axios.post(`${BASE_URL}/admin/set_default_model`, { model });
  return res.data;
}

export async function generatePipeline(req: GenerateRequest): Promise<GenerateResponse> {
  const res = await axios.post(`${BASE_URL}/llm/generate`, req);
  return res.data;
}

export async function batchGenerate(reqs: GenerateRequest[]) {
  const res = await axios.post(`${BASE_URL}/llm/batch_generate`, reqs);
  return res.data;
}

export async function getHistory(limit = 20, offset = 0) {
  const res = await axios.get(`${BASE_URL}/llm/llm_history`, {
    params: { limit, offset }
  });
  return res.data;
}

// Для RAG и других расширений:
export async function ragGenerate(payload: any) {
  const res = await axios.post(`${BASE_URL}/llm/rag_generate`, payload);
  return res.data;
}

export async function importDocs(docs: any[]) {
  const res = await axios.post(`${BASE_URL}/admin/import_docs`, docs);
  return res.data;
}
export async function getAppConfig(): Promise<any> {
  const resp = await axios.get("/admin/app_config");
  return resp.data;
}

// Сохранить глобальные настройки
export async function setAppConfig(config: any): Promise<any> {
  const resp = await axios.post("/admin/set_app_config", config);
  return resp.data;
}

export async function getPrometheusMetrics(): Promise<string> {
  const resp = await axios.get(`${BASE_URL}/metrics/prometheus`, { responseType: "text" });
  return resp.data;
}

