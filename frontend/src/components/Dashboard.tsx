'use client';

import { SummaryResponse, formatCurrency, formatNumber, formatPercent } from '@/lib/api';

interface DashboardProps {
  summary: SummaryResponse;
}

export function Dashboard({ summary }: DashboardProps) {
  const matchRate = summary.total_orders > 0 
    ? (summary.matched_orders / summary.total_orders * 100) 
    : 0;
  
  const riskRate = summary.total_revenue > 0
    ? (summary.revenue_at_risk / summary.total_revenue * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Hero Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Orders"
          value={formatNumber(summary.total_orders)}
          color="slate"
        />
        <StatCard
          label="Total Revenue"
          value={formatCurrency(summary.total_revenue)}
          color="teal"
        />
        <StatCard
          label="Revenue at Risk"
          value={formatCurrency(summary.revenue_at_risk)}
          subtext={`${riskRate.toFixed(1)}% of total`}
          color="amber"
        />
        <StatCard
          label="Rodent Revenue"
          value={formatCurrency(summary.rodent_revenue)}
          subtext={`${summary.rodent_restaurant_count} restaurants`}
          color="red"
        />
      </div>

      {/* Match Rate Bar */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm text-slate-500">Data Match Rate</span>
          <span className="text-sm font-medium text-slate-700">
            {formatNumber(summary.matched_orders)} / {formatNumber(summary.total_orders)} orders matched
          </span>
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div 
            className="h-full bg-teal-500 rounded-full transition-all duration-1000"
            style={{ width: `${matchRate}%` }}
          />
        </div>
        <div className="flex justify-between mt-2 text-xs text-slate-400">
          <span>0%</span>
          <span className="text-teal-600 font-medium">{formatPercent(matchRate)} matched</span>
          <span>100%</span>
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  subtext?: string;
  color: 'slate' | 'teal' | 'amber' | 'red';
}

function StatCard({ label, value, subtext, color }: StatCardProps) {
  const textColors = {
    slate: 'text-slate-700',
    teal: 'text-teal-600',
    amber: 'text-amber-600',
    red: 'text-red-600',
  };

  return (
    <div className="card p-5">
      <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
        {label}
      </p>
      <p className={`text-2xl font-semibold ${textColors[color]}`}>
        {value}
      </p>
      {subtext && (
        <p className="text-xs text-slate-400 mt-1">{subtext}</p>
      )}
    </div>
  );
}
