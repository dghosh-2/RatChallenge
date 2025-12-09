'use client';

import { useQuery } from '@tanstack/react-query';
import { api, formatCurrency, formatNumber, DateRangeDays } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts';

const CATEGORY_CONFIG: Record<string, { label: string; color: string }> = {
  closed: { label: 'Closed', color: '#dc2626' },
  grade_c: { label: 'Grade C', color: '#ea580c' },
  grade_pending: { label: 'Pending', color: '#d97706' },
  critical_violation: { label: 'Critical', color: '#b91c1c' },
};

interface RevenueAtRiskProps {
  days?: DateRangeDays;
}

export function RevenueAtRisk({ days = 90 }: RevenueAtRiskProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['revenue-at-risk', days],
    queryFn: () => api.getRevenueAtRisk(days),
  });

  if (isLoading) {
    return <CardSkeleton title="Revenue at Risk (RAR)" />;
  }

  if (!data) return null;

  const chartData = Object.entries(data.breakdown)
    .filter(([_, value]) => value > 0)
    .map(([key, value]) => ({
      category: CATEGORY_CONFIG[key]?.label || key,
      value,
      color: CATEGORY_CONFIG[key]?.color || '#64748b',
      orders: data.risk_categories[key] || 0,
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="card">
      <div className="p-5">
        <h2 className="text-base font-semibold text-slate-800">Revenue at Risk (RAR)</h2>
        <p className="text-sm text-slate-400 mt-0.5">
          Orders from restaurants with health concerns
        </p>
      </div>

      {/* Total RAR Highlight */}
      <div className="px-5 pb-4">
        <div className="p-4 bg-amber-50 rounded-lg">
          <p className="text-2xl font-semibold text-amber-600">
            {formatCurrency(data.total_revenue_at_risk)}
          </p>
          <p className="text-sm text-slate-500 mt-1">
            {formatNumber(data.order_count)} orders at risk
          </p>
        </div>
      </div>

      {/* Breakdown Chart */}
      <div className="px-5 pb-5">
        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <XAxis 
                type="number" 
                tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis 
                type="category" 
                dataKey="category" 
                width={65}
                tick={{ fill: '#64748b', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white shadow-lg rounded-lg p-3 text-sm">
                        <p className="font-medium text-slate-800">{data.category}</p>
                        <p className="text-amber-600">
                          {formatCurrency(data.value)}
                        </p>
                        <p className="text-xs text-slate-400">
                          {formatNumber(data.orders)} orders
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Categories Legend */}
        <div className="grid grid-cols-2 gap-2 mt-4">
          {chartData.map((item) => (
            <div key={item.category} className="flex items-center gap-2">
              <div 
                className="w-2.5 h-2.5 rounded"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-xs text-slate-500">
                {item.category}: {formatNumber(item.orders)} orders
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function CardSkeleton({ title }: { title: string }) {
  return (
    <div className="card">
      <div className="p-5">
        <h2 className="text-base font-semibold text-slate-800">{title}</h2>
      </div>
      <div className="px-5 pb-5">
        <div className="skeleton h-48 w-full rounded" />
      </div>
    </div>
  );
}
