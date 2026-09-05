const API_BASE = '/api';

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

export const api = {
  health: () => fetchApi<{ status: string; database: string; gemini_configured: boolean }>('/health'),
  
  dashboard: () => fetchApi<any>('/dashboard'),
  
  stores: () => fetchApi<any[]>('/stores'),
  
  products: (category?: string) => fetchApi<any[]>(`/products${category ? `?category=${category}` : ''}`),
  
  inventory: (params?: { store_id?: number; product_id?: number; category?: string; risk?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.store_id) searchParams.set('store_id', params.store_id.toString());
    if (params?.product_id) searchParams.set('product_id', params.product_id.toString());
    if (params?.category) searchParams.set('category', params.category);
    if (params?.risk) searchParams.set('risk', params.risk);
    return fetchApi<any[]>(`/inventory?${searchParams.toString()}`);
  },
  
  sales: (days = 30, store_id?: number, category?: string) => {
    const params = new URLSearchParams({ days: days.toString() });
    if (store_id) params.set('store_id', store_id.toString());
    if (category) params.set('category', category);
    return fetchApi<any[]>(`/sales?${params.toString()}`);
  },
  
  risks: (params?: { store_id?: number; category?: string; level?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.store_id) searchParams.set('store_id', params.store_id.toString());
    if (params?.category) searchParams.set('category', params.category);
    if (params?.level) searchParams.set('level', params.level);
    return fetchApi<any[]>(`/risks?${searchParams.toString()}`);
  },
  
  overstock: (params?: { store_id?: number; category?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.store_id) searchParams.set('store_id', params.store_id.toString());
    if (params?.category) searchParams.set('category', params.category);
    return fetchApi<any[]>(`/overstock?${searchParams.toString()}`);
  },
  
  anomalies: (params?: { store_id?: number; category?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.store_id) searchParams.set('store_id', params.store_id.toString());
    if (params?.category) searchParams.set('category', params.category);
    return fetchApi<any[]>(`/anomalies?${searchParams.toString()}`);
  },
  
  recommendations: (params?: { store_id?: number; product_id?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.store_id) searchParams.set('store_id', params.store_id.toString());
    if (params?.product_id) searchParams.set('product_id', params.product_id.toString());
    return fetchApi<any[]>(`/recommendations?${searchParams.toString()}`);
  },

  storePerformance: () => fetchApi<any[]>('/stores/performance'),
  
  topProducts: (limit = 10) => fetchApi<any[]>(`/products/top?limit=${limit}`),

  attention: () => fetchApi<any>('/attention'),
  
  product: (id: number) => fetchApi<any>(`/products/${id}`),
  
  store: (id: number) => fetchApi<any>(`/stores/${id}`),
  
  copilot: (question: string) => fetchApi<any>('/copilot/query', {
    method: 'POST',
    body: JSON.stringify({ question }),
  }),
};