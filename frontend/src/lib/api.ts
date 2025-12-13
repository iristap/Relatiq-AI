import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  paramsSerializer: {
    indexes: null // This might require 'qs' library if axios version is old, but newer axios supports this or custom function.
    // Let's use a custom function to be safe and dependency-free.
  }
});

// Overwriting with custom function
api.defaults.paramsSerializer = (params) => {
  const searchParams = new URLSearchParams();
  for (const key in params) {
    const value = params[key];
    if (Array.isArray(value)) {
      value.forEach(v => searchParams.append(key, v));
    } else if (value !== undefined && value !== null) {
      searchParams.append(key, value);
    }
  }
  return searchParams.toString();
};

export interface Article {
  title: string;
  date: string;
  source?: string;
  url?: string;
  tier?: string;
  status?: string;
}

export interface GraphNode {
  id: string;
  label: string;
  color: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const getArticles = async (params?: {
  date_range?: string,
  tiers?: string[],
  news_status?: string[],
  sectors?: string[],
  entity_search?: string
}) => {
  const response = await api.get<Article[]>('/articles', { params });
  return response.data;
};

export const getNetwork = async (params: {
  article_titles?: string[],
  node_types?: string[],
  rel_types?: string[],
  date_range?: string,
  tiers?: string[],
  news_status?: string[],
  sectors?: string[],
  entity_search?: string
}) => {
  const response = await api.get<GraphData>('/graph/network', { params });
  return response.data;
};

export const getSectors = async () => {
  const response = await api.get<string[]>('/sectors');
  return response.data;
};

export const getCompanyAnalysis = async (article_titles: string[]) => {
  const response = await api.get('/analysis/companies', { params: { article_titles } });
  return response.data;
};

export const getArticleMentions = async (title: string) => {
  const response = await api.get<string[]>('/articles/mentions', { params: { title } });
  return response.data;
};

export const getArticleContent = async (title: string) => {
  const response = await api.get<{ text: string }>('/article/content', { params: { title } });
  return response.data;
};

export const agentQuery = async (query: string) => {
  const response = await api.post('/agent/query', { query });
  return response.data;
};

export const agentInsight = async (articleTitles: string[], analysisType: string = "Summary") => {
  const response = await api.post('/agent/insight', { article_titles: articleTitles, analysis_type: analysisType });
  return response.data;
};
