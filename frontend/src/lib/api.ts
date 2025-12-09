/**
 * API client for RatChallenge backend
 */

// Use environment variable in production, fallback to proxy in development
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

export interface HealthResponse {
  status: string;
  orders_loaded: number;
  inspections_loaded: number;
  restaurants_mapped: number;
}

export interface GradeRevenue {
  grade: string;
  revenue: number;
  order_count: number;
  percentage: number;
}

export interface RevenueByGradeResponse {
  total_revenue: number;
  grades: GradeRevenue[];
  unmatched_revenue: number;
  unmatched_order_count: number;
}

export interface RodentOrder {
  order_id: number;
  restaurant_name: string;
  cost: number;
  violation_description: string;
  inspection_date: string;
  camis: string;
}

export interface RodentOrdersResponse {
  total_rodent_revenue: number;
  order_count: number;
  unique_restaurants: number;
  orders: RodentOrder[];
}

export interface RevenueAtRiskResponse {
  total_revenue_at_risk: number;
  order_count: number;
  breakdown: Record<string, number>;
  risk_categories: Record<string, number>;
}

export interface BoroughRevenue {
  borough: string;
  revenue: number;
  order_count: number;
  percentage: number;
  top_violation_category: string | null;
}

export interface BoroughBreakdownResponse {
  total_revenue: number;
  boroughs: BoroughRevenue[];
  violation_categories: Record<string, number>;
}

export interface WatchlistRestaurant {
  rank: number;
  restaurant_name: string;
  camis: string;
  revenue: number;
  order_count: number;
  latest_grade: string | null;
  critical_violations: number;
  rodent_violations: number;
  last_inspection_date: string | null;
  risk_flags: string[];
}

export interface WatchlistResponse {
  restaurants: WatchlistRestaurant[];
  total_watchlist_revenue: number;
}

export interface SummaryResponse {
  total_orders: number;
  total_revenue: number;
  matched_orders: number;
  matched_revenue: number;
  rodent_revenue: number;
  rodent_order_count: number;
  rodent_restaurant_count: number;
  revenue_at_risk: number;
  risk_order_count: number;
  grade_breakdown: Record<string, number>;
  borough_breakdown: Record<string, number>;
  top_watchlist: WatchlistRestaurant[];
}

async function fetchApi<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`);
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
}

export const api = {
  getHealth: () => fetchApi<HealthResponse>('/health'),
  
  getSummary: () => fetchApi<SummaryResponse>('/analytics/summary'),
  
  getRodentOrders: () => fetchApi<RodentOrdersResponse>('/analytics/rodent-orders'),
  
  getRevenueByGrade: () => fetchApi<RevenueByGradeResponse>('/analytics/revenue-by-grade'),
  
  getRevenueAtRisk: () => fetchApi<RevenueAtRiskResponse>('/analytics/revenue-at-risk'),
  
  getBoroughBreakdown: () => fetchApi<BoroughBreakdownResponse>('/analytics/borough-breakdown'),
  
  getWatchlist: (topN: number = 10) => 
    fetchApi<WatchlistResponse>(`/analytics/watchlist?top_n=${topN}`),
  
  downloadPdf: async () => {
    try {
      const response = await fetch(`${API_BASE}/report/pdf`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to download PDF: ${response.status} ${response.statusText}`);
      }
      const blob = await response.blob();
      
      // Check if blob is valid
      if (blob.size === 0) {
        throw new Error('Received empty PDF file');
      }
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'rat_challenge_report.pdf';
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);
    } catch (error) {
      console.error('PDF download error:', error);
      throw error;
    }
  },
};

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}


