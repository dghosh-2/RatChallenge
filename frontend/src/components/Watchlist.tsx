'use client';

import { useQuery } from '@tanstack/react-query';
import { api, formatCurrency, formatNumber } from '@/lib/api';

export function Watchlist() {
  const { data, isLoading } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => api.getWatchlist(10),
  });

  if (isLoading) {
    return (
      <div className="card">
        <div className="p-5">
          <h2 className="text-base font-semibold text-slate-800">Top 10 Watchlist</h2>
        </div>
        <div className="px-5 pb-5">
          <div className="skeleton h-64 w-full rounded" />
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="card">
      <div className="p-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-800">Top 10 Watchlist</h2>
            <p className="text-sm text-slate-400 mt-0.5">
              Highest-earning restaurants with open health risk flags
            </p>
          </div>
          <div className="text-right">
            <p className="text-xl font-semibold text-red-600">
              {formatCurrency(data.total_watchlist_revenue)}
            </p>
            <p className="text-xs text-slate-400">Combined Revenue</p>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="w-12">#</th>
              <th>Restaurant</th>
              <th className="text-right">Revenue</th>
              <th className="text-center">Grade</th>
              <th className="text-center">Critical</th>
              <th className="text-center">Rodent</th>
              <th>Risk Flags</th>
            </tr>
          </thead>
          <tbody>
            {data.restaurants.map((restaurant) => (
              <tr key={restaurant.camis} className="group">
                <td className="font-mono text-slate-400">
                  {restaurant.rank}
                </td>
                <td>
                  <div>
                    <p className="font-medium text-slate-700 group-hover:text-red-600 transition-colors">
                      {restaurant.restaurant_name}
                    </p>
                    <p className="text-xs text-slate-400">
                      {restaurant.order_count} orders · Last inspected: {restaurant.last_inspection_date || 'N/A'}
                    </p>
                  </div>
                </td>
                <td className="text-right">
                  <span className="font-medium text-red-600">
                    {formatCurrency(restaurant.revenue)}
                  </span>
                </td>
                <td className="text-center">
                  <GradeBadge grade={restaurant.latest_grade} />
                </td>
                <td className="text-center">
                  {restaurant.critical_violations > 0 ? (
                    <span className="badge badge-danger">
                      {restaurant.critical_violations}
                    </span>
                  ) : (
                    <span className="text-slate-300">—</span>
                  )}
                </td>
                <td className="text-center">
                  {restaurant.rodent_violations > 0 ? (
                    <span className="badge badge-danger">
                      {restaurant.rodent_violations}
                    </span>
                  ) : (
                    <span className="text-slate-300">—</span>
                  )}
                </td>
                <td>
                  <div className="flex flex-wrap gap-1">
                    {restaurant.risk_flags.slice(0, 3).map((flag, i) => (
                      <span key={i} className="badge badge-warning text-xs">
                        {flag}
                      </span>
                    ))}
                    {restaurant.risk_flags.length > 3 && (
                      <span className="badge badge-info text-xs">
                        +{restaurant.risk_flags.length - 3}
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.restaurants.length === 0 && (
        <div className="p-12 text-center text-slate-400">
          <p>No restaurants with risk flags found</p>
        </div>
      )}
    </div>
  );
}

function GradeBadge({ grade }: { grade: string | null }) {
  if (!grade) {
    return <span className="badge bg-slate-100 text-slate-500">N/A</span>;
  }

  const gradeStyles: Record<string, string> = {
    A: 'bg-emerald-50 text-emerald-700',
    B: 'bg-amber-50 text-amber-700',
    C: 'bg-red-50 text-red-700',
    Z: 'bg-slate-100 text-slate-600',
    P: 'bg-violet-50 text-violet-700',
    N: 'bg-slate-100 text-slate-500',
  };

  return (
    <span className={`badge ${gradeStyles[grade] || gradeStyles.N}`}>
      {grade}
    </span>
  );
}
