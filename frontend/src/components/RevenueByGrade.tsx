'use client';

import { useQuery } from '@tanstack/react-query';
import { api, formatCurrency, formatPercent, DateRangeDays } from '@/lib/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const GRADE_COLORS: Record<string, string> = {
  A: '#059669',
  B: '#d97706',
  C: '#dc2626',
  Z: '#64748b',
  P: '#7c3aed',
  N: '#94a3b8',
};

const GRADE_LABELS: Record<string, string> = {
  A: 'Grade A (Best)',
  B: 'Grade B',
  C: 'Grade C (Worst)',
  Z: 'Grade Pending',
  P: 'Pending',
  N: 'Not Yet Graded',
};

interface RevenueByGradeProps {
  days?: DateRangeDays;
}

export function RevenueByGrade({ days = 90 }: RevenueByGradeProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['revenue-by-grade', days],
    queryFn: () => api.getRevenueByGrade(days),
  });

  if (isLoading) {
    return <CardSkeleton title="Revenue by Health Grade" />;
  }

  if (!data) return null;

  const chartData = data.grades.map((g) => ({
    name: GRADE_LABELS[g.grade] || g.grade,
    value: g.revenue,
    grade: g.grade,
    percentage: g.percentage,
    orders: g.order_count,
  }));

  return (
    <div className="card">
      <div className="p-5">
        <h2 className="text-base font-semibold text-slate-800">Revenue by Health Grade</h2>
        <p className="text-sm text-slate-400 mt-0.5">
          Order revenue split by NYC inspection grade
        </p>
      </div>

      <div className="px-5 pb-5">
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={75}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={GRADE_COLORS[entry.grade] || '#94a3b8'}
                    stroke="transparent"
                  />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white shadow-lg rounded-lg p-3 text-sm">
                        <p className="font-medium text-slate-800">{data.name}</p>
                        <p className="text-slate-600">
                          {formatCurrency(data.value)}
                        </p>
                        <p className="text-xs text-slate-400">
                          {data.orders} orders ({formatPercent(data.percentage)})
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 gap-2 mt-4">
          {data.grades.map((grade) => (
            <div key={grade.grade} className="flex items-center gap-2">
              <div 
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: GRADE_COLORS[grade.grade] || '#94a3b8' }}
              />
              <span className="text-xs text-slate-500">
                {grade.grade}: {formatCurrency(grade.revenue)}
              </span>
            </div>
          ))}
        </div>

        {/* Unmatched note */}
        {data.unmatched_revenue > 0 && (
          <div className="mt-4 p-3 bg-slate-50 rounded-lg">
            <p className="text-xs text-slate-500">
              <span className="text-slate-600 font-medium">
                {formatCurrency(data.unmatched_revenue)}
              </span>{' '}
              from {data.unmatched_order_count} orders could not be matched
            </p>
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
