import axios from 'axios';

export const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

export interface Trace {
    id: string;
    user_message: string;
    bot_response: string;
    category: string;
    timestamp: string;
    response_time_ms: number;
}

export const createTrace = async (user_message: string): Promise<Trace> => {
    const { data } = await apiClient.post<Trace>('/traces/', { user_message });
    return data;
};

export const fetchTraces = async (category?: string): Promise<Trace[]> => {
    const params = category && category !== 'All' ? { category } : {};
    const { data } = await apiClient.get<Trace[]>('/traces/', { params });
    return data;
};

export interface AnalyticsData {
    total_traces: number;
    average_response_time_ms: number;
    category_breakdown: {
        category: string;
        count: number;
        percentage: number;
    }[];
}

export const fetchAnalytics = async (): Promise<AnalyticsData> => {
    const { data } = await apiClient.get<AnalyticsData>('/analytics/');
    return data;
};
