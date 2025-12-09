'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Dashboard } from '@/components/Dashboard';
import { RevenueByGrade } from '@/components/RevenueByGrade';
import { RodentOrders } from '@/components/RodentOrders';
import { RevenueAtRisk } from '@/components/RevenueAtRisk';
import { BoroughBreakdown } from '@/components/BoroughBreakdown';
import { Watchlist } from '@/components/Watchlist';

export default function Home() {
  const dateRange = 90;

  const { data: summary, isLoading, error } = useQuery({
    queryKey: ['summary', dateRange],
    queryFn: () => api.getSummary(dateRange),
  });

  const handleDownloadPdf = async () => {
    try {
      await api.downloadPdf(dateRange);
    } catch (err) {
      console.error('Failed to download PDF:', err);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="card p-8 max-w-md text-center">
          <h2 className="text-lg font-semibold text-red-600 mb-2">Connection Error</h2>
          <p className="text-slate-500 mb-4">
            Unable to connect to the API. Make sure the backend server is running.
          </p>
          <code className="text-xs text-slate-600 bg-slate-100 px-3 py-2 rounded block font-mono">
            cd backend && uvicorn main:app --reload
          </code>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div>
              <h1 className="text-lg font-semibold text-slate-800">Food Safety Analytics</h1>
              <p className="text-xs text-slate-400">NYC Restaurant Risk Dashboard</p>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={handleDownloadPdf}
                className="btn btn-primary flex items-center gap-2"
                disabled={isLoading}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Download Report
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <LoadingSkeleton />
        ) : summary ? (
          <div className="space-y-6 animate-fade-in">
            {/* Summary Stats */}
            <Dashboard summary={summary} />
            
            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Rodent Analysis */}
              <RodentOrders days={dateRange} />
              
              {/* Revenue by Grade */}
              <RevenueByGrade days={dateRange} />
              
              {/* Revenue at Risk */}
              <RevenueAtRisk days={dateRange} />
              
              {/* Borough Breakdown */}
              <BoroughBreakdown days={dateRange} />
            </div>
            
            {/* Watchlist - Full Width */}
            <Watchlist days={dateRange} />
          </div>
        ) : null}
      </div>

      {/* Footer */}
      <footer className="mt-12 py-6 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-slate-400 text-sm">
          <p>Data sourced from NYC DOHMH Restaurant Inspection Results</p>
        </div>
      </footer>
    </main>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Stats skeleton */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card p-6">
            <div className="skeleton h-3 w-20 mb-3 rounded" />
            <div className="skeleton h-7 w-28 rounded" />
          </div>
        ))}
      </div>
      
      {/* Cards skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card p-6 h-80">
            <div className="skeleton h-5 w-40 mb-4 rounded" />
            <div className="skeleton h-48 w-full rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
