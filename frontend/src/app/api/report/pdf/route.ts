import { NextResponse } from 'next/server';

// PDF generation is handled client-side due to Vercel serverless limitations
// This endpoint returns the analytics data for client-side PDF generation
import analyticsData from '../../../../../public/analytics-data.json';

export async function GET() {
  // Return all data needed for PDF generation
  return NextResponse.json({
    summary: analyticsData.summary,
    rodent_orders: analyticsData.rodent_orders,
    revenue_by_grade: analyticsData.revenue_by_grade,
    revenue_at_risk: analyticsData.revenue_at_risk,
    borough_breakdown: analyticsData.borough_breakdown,
    watchlist: analyticsData.watchlist,
  });
}

