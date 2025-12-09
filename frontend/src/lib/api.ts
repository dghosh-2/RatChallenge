/**
 * API client for RatChallenge backend
 */

import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

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
      // Fetch all data needed for PDF
      const [summary, rodentOrders, revenueByGrade, revenueAtRisk, boroughBreakdown, watchlist] = await Promise.all([
        api.getSummary(),
        api.getRodentOrders(),
        api.getRevenueByGrade(),
        api.getRevenueAtRisk(),
        api.getBoroughBreakdown(),
        api.getWatchlist(10),
      ]);

      // Generate PDF client-side
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth();
      
      // Title
      doc.setFontSize(24);
      doc.setTextColor(26, 26, 46);
      doc.text('Food Safety Risk Analysis Report', pageWidth / 2, 30, { align: 'center' });
      
      doc.setFontSize(12);
      doc.setTextColor(100, 100, 100);
      doc.text(`Generated: ${new Date().toLocaleDateString()}`, pageWidth / 2, 40, { align: 'center' });
      
      // Executive Summary
      doc.setFontSize(16);
      doc.setTextColor(26, 26, 46);
      doc.text('Executive Summary', 14, 60);
      
      doc.setFontSize(10);
      doc.setTextColor(50, 50, 50);
      const summaryText = [
        `Total Orders: ${formatNumber(summary.total_orders)}`,
        `Total Revenue: ${formatCurrency(summary.total_revenue)}`,
        `Matched Orders: ${formatNumber(summary.matched_orders)}`,
        `Revenue at Risk: ${formatCurrency(summary.revenue_at_risk)}`,
        `Rodent Revenue: ${formatCurrency(summary.rodent_revenue)} from ${summary.rodent_restaurant_count} restaurants`,
      ];
      
      let y = 70;
      summaryText.forEach(text => {
        doc.text(text, 14, y);
        y += 7;
      });
      
      // Revenue by Grade Table
      doc.setFontSize(16);
      doc.setTextColor(26, 26, 46);
      doc.text('Revenue by Health Grade', 14, y + 10);
      
      autoTable(doc, {
        startY: y + 15,
        head: [['Grade', 'Revenue', 'Orders', '% of Total']],
        body: revenueByGrade.grades.map(g => [
          g.grade,
          formatCurrency(g.revenue),
          formatNumber(g.order_count),
          `${g.percentage.toFixed(1)}%`,
        ]),
        theme: 'striped',
        headStyles: { fillColor: [26, 26, 46] },
      });
      
      // New page for Revenue at Risk
      doc.addPage();
      
      doc.setFontSize(16);
      doc.setTextColor(26, 26, 46);
      doc.text('Revenue at Risk (RAR)', 14, 20);
      
      doc.setFontSize(24);
      doc.setTextColor(220, 38, 38);
      doc.text(formatCurrency(revenueAtRisk.total_revenue_at_risk), 14, 35);
      
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      doc.text(`${formatNumber(revenueAtRisk.order_count)} orders affected`, 14, 43);
      
      const categoryLabels: Record<string, string> = {
        closed: 'Closed/Re-closed',
        grade_c: 'Grade C',
        grade_pending: 'Pending Grades',
        critical_violation: 'Critical Violations',
      };
      
      autoTable(doc, {
        startY: 50,
        head: [['Risk Category', 'Revenue', 'Orders']],
        body: Object.entries(revenueAtRisk.breakdown).map(([key, value]) => [
          categoryLabels[key] || key,
          formatCurrency(value),
          formatNumber(revenueAtRisk.risk_categories[key] || 0),
        ]),
        theme: 'striped',
        headStyles: { fillColor: [220, 38, 38] },
      });
      
      // Borough Breakdown
      const finalY = (doc as jsPDF & { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY || 100;
      
      doc.setFontSize(16);
      doc.setTextColor(26, 26, 46);
      doc.text('Borough Breakdown', 14, finalY + 15);
      
      autoTable(doc, {
        startY: finalY + 20,
        head: [['Borough', 'Revenue', 'Orders', '% of Total']],
        body: boroughBreakdown.boroughs.map(b => [
          b.borough,
          formatCurrency(b.revenue),
          formatNumber(b.order_count),
          `${b.percentage.toFixed(1)}%`,
        ]),
        theme: 'striped',
        headStyles: { fillColor: [15, 118, 110] },
      });
      
      // New page for Watchlist
      doc.addPage();
      
      doc.setFontSize(16);
      doc.setTextColor(26, 26, 46);
      doc.text('Top 10 Watchlist - Highest Earning Restaurants with Risk Flags', 14, 20);
      
      autoTable(doc, {
        startY: 30,
        head: [['#', 'Restaurant', 'Revenue', 'Grade', 'Risk Flags']],
        body: watchlist.restaurants.map(r => [
          r.rank.toString(),
          r.restaurant_name.slice(0, 25),
          formatCurrency(r.revenue),
          r.latest_grade || 'N/A',
          r.risk_flags.slice(0, 2).join(', '),
        ]),
        theme: 'striped',
        headStyles: { fillColor: [220, 38, 38] },
        columnStyles: {
          0: { cellWidth: 10 },
          1: { cellWidth: 50 },
          4: { cellWidth: 60 },
        },
      });
      
      // Rodent Analysis
      const watchlistFinalY = (doc as jsPDF & { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY || 150;
      
      doc.setFontSize(16);
      doc.setTextColor(26, 26, 46);
      doc.text('Rodent Violation Analysis', 14, watchlistFinalY + 15);
      
      doc.setFontSize(10);
      doc.setTextColor(50, 50, 50);
      doc.text(`Total Rodent Revenue: ${formatCurrency(rodentOrders.total_rodent_revenue)}`, 14, watchlistFinalY + 25);
      doc.text(`Affected Orders: ${formatNumber(rodentOrders.order_count)}`, 14, watchlistFinalY + 32);
      doc.text(`Unique Restaurants: ${rodentOrders.unique_restaurants}`, 14, watchlistFinalY + 39);
      
      // Footer
      const pageCount = doc.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(150, 150, 150);
        doc.text(
          `Page ${i} of ${pageCount} | Data sourced from NYC DOHMH Restaurant Inspection Results`,
          pageWidth / 2,
          doc.internal.pageSize.getHeight() - 10,
          { align: 'center' }
        );
      }
      
      // Save PDF
      doc.save('food_safety_report.pdf');
    } catch (error) {
      console.error('PDF generation error:', error);
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
