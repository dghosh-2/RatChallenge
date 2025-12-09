'use client';

import { useQuery } from '@tanstack/react-query';
import { api, formatCurrency, formatPercent, formatNumber, DateRangeDays } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts';

const BOROUGH_COLORS: Record<string, string> = {
  MANHATTAN: '#7c3aed',
  BROOKLYN: '#0891b2',
  QUEENS: '#059669',
  BRONX: '#ea580c',
  'STATEN ISLAND': '#db2777',
};

interface BoroughBreakdownProps {
  days?: DateRangeDays;
}

export function BoroughBreakdown({ days = 90 }: BoroughBreakdownProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['borough-breakdown', days],
    queryFn: () => api.getBoroughBreakdown(days),
  });

  if (isLoading) {
    return <CardSkeleton title="Borough Breakdown" />;
  }

  if (!data) return null;

  const chartData = data.boroughs
    .filter((b) => b.borough && b.revenue > 0)
    .map((b) => ({
      name: b.borough,
      revenue: b.revenue,
      orders: b.order_count,
      percentage: b.percentage,
      color: BOROUGH_COLORS[b.borough] || '#64748b',
    }))
    .sort((a, b) => b.revenue - a.revenue);

  return (
    <div className="card">
      <div className="p-5">
        <h2 className="text-base font-semibold text-slate-800">Borough Breakdown</h2>
        <p className="text-sm text-slate-400 mt-0.5">
          Order revenue distribution across NYC boroughs
        </p>
      </div>

      <div className="px-5 pb-5">
        {chartData.length > 0 ? (
          <>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <XAxis 
                    dataKey="name" 
                    tick={{ fill: '#64748b', fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => v.slice(0, 3)}
                  />
                  <YAxis 
                    tickFormatter={(v) => v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v.toFixed(0)}`}
                    tick={{ fill: '#94a3b8', fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    width={45}
                    allowDecimals={false}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white shadow-lg rounded-lg p-3 text-sm">
                            <p className="font-medium text-slate-800">{data.name}</p>
                            <p style={{ color: data.color }}>
                              {formatCurrency(data.revenue)}
                            </p>
                            <p className="text-xs text-slate-400">
                              {formatNumber(data.orders)} orders ({formatPercent(data.percentage)})
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Borough List */}
            <div className="mt-4 space-y-2">
              {chartData.map((boro) => (
                <div 
                  key={boro.name}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: boro.color }}
                    />
                    <span className="text-sm text-slate-600">{boro.name}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium" style={{ color: boro.color }}>
                      {formatCurrency(boro.revenue)}
                    </span>
                    <span className="text-xs text-slate-400 ml-2">
                      ({formatPercent(boro.percentage)})
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="text-center py-8 text-slate-400">
            <p>No borough data available</p>
          </div>
        )}

        {/* Violation Categories */}
        {Object.keys(data.violation_categories).length > 0 && (
          <div className="mt-6 pt-4">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
              Revenue by Violation Type
            </p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(data.violation_categories)
                .sort(([, a], [, b]) => b - a)
                .map(([category, revenue]) => (
                  <div key={category} className="flex items-center justify-between">
                    <span className="text-xs text-slate-500 capitalize">{category}</span>
                    <span className="text-xs font-medium text-slate-600">
                      {formatCurrency(revenue)}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        )}
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
