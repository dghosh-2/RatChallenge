/**
 * API client for RatChallenge backend
 */

// Use environment variable in production, fallback to /api for development
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

// Supported date ranges
export type DateRangeDays = 7 | 30 | 90;

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
    const errorBody = await response.text();
    let errorMessage = `API error: ${response.status} ${response.statusText}`;
    try {
      const errorJson = JSON.parse(errorBody);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      errorMessage = errorBody || errorMessage;
    }
    throw new Error(errorMessage);
  }
  
  return response.json();
}

export const api = {
  getHealth: (days: DateRangeDays = 90) => 
    fetchApi<HealthResponse>(`/health?days=${days}`),
  
  getSummary: (days: DateRangeDays = 90) => 
    fetchApi<SummaryResponse>(`/analytics/summary?days=${days}`),
  
  getRodentOrders: (days: DateRangeDays = 90) => 
    fetchApi<RodentOrdersResponse>(`/analytics/rodent-orders?days=${days}`),
  
  getRevenueByGrade: (days: DateRangeDays = 90) => 
    fetchApi<RevenueByGradeResponse>(`/analytics/revenue-by-grade?days=${days}`),
  
  getRevenueAtRisk: (days: DateRangeDays = 90) => 
    fetchApi<RevenueAtRiskResponse>(`/analytics/revenue-at-risk?days=${days}`),
  
  getBoroughBreakdown: (days: DateRangeDays = 90) => 
    fetchApi<BoroughBreakdownResponse>(`/analytics/borough-breakdown?days=${days}`),
  
  getWatchlist: (days: DateRangeDays = 90, topN: number = 10) => 
    fetchApi<WatchlistResponse>(`/analytics/watchlist?days=${days}&top_n=${topN}`),
  
  downloadPdf: async (days: DateRangeDays = 90) => {
    try {
      const response = await fetch(`${API_BASE}/report/pdf?days=${days}`);
      if (!response.ok) {
        const errorBody = await response.text();
        let errorMessage = 'Failed to download PDF';
        try {
          const errorJson = JSON.parse(errorBody);
          errorMessage = errorJson.detail || errorMessage;
        } catch {
          errorMessage = errorBody || errorMessage;
        }
        throw new Error(errorMessage);
      }
      const blob = await response.blob();
      
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
