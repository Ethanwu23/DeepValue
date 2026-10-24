export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:2024";
export interface ModelConfig {
  model_id: string;
  display_name: string;
  icon: string;
  icon_color: string;
}
export async function fetchAvailableModels(): Promise<ModelConfig[]> {
  const response = await fetch(`${API_BASE_URL}/api/models`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const data = await response.json();
  if (!Array.isArray(data.models)) throw new Error("模型列表格式错误");
  return data.models;
}
