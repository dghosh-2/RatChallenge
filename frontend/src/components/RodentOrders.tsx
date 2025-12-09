'use client';

import { useQuery } from '@tanstack/react-query';
import { api, formatCurrency, formatNumber, DateRangeDays } from '@/lib/api';

interface RodentOrdersProps {
  days?: DateRangeDays;
}

export function RodentOrders({ days = 90 }: RodentOrdersProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['rodent-orders', days],
    queryFn: () => api.getRodentOrders(days),
  });

  if (isLoading) {
    return <CardSkeleton title="Rodent Violation Analysis" />;
  }

  if (!data) return null;

  return (
    <div className="card">
      <div className="p-5">
        <h2 className="text-base font-semibold text-slate-800">Rodent Violation Analysis</h2>
        <p className="text-sm text-slate-400 mt-0.5">
          Orders from restaurants with documented rodent violations
        </p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 bg-red-50">
        <div className="p-4 text-center">
          <p className="text-xl font-semibold text-red-600">
            {formatCurrency(data.total_rodent_revenue)}
          </p>
          <p className="text-xs text-slate-500 mt-1">Total Revenue</p>
        </div>
        <div className="p-4 text-center">
          <p className="text-xl font-semibold text-red-600">
            {formatNumber(data.order_count)}
          </p>
          <p className="text-xs text-slate-500 mt-1">Orders</p>
        </div>
        <div className="p-4 text-center">
          <p className="text-xl font-semibold text-red-600">
            {data.unique_restaurants}
          </p>
          <p className="text-xs text-slate-500 mt-1">Restaurants</p>
        </div>
      </div>

      {/* Orders Table */}
      <div className="max-h-64 overflow-y-auto">
        <table className="data-table">
          <thead className="sticky top-0">
            <tr>
              <th>Restaurant</th>
              <th className="text-right">Cost</th>
              <th className="text-right">Date</th>
            </tr>
          </thead>
          <tbody>
            {data.orders.slice(0, 10).map((order) => (
              <tr key={order.order_id}>
                <td className="font-medium text-slate-700">
                  {order.restaurant_name.length > 25 
                    ? `${order.restaurant_name.slice(0, 25)}...` 
                    : order.restaurant_name}
                </td>
                <td className="text-right text-red-600">
                  {formatCurrency(order.cost)}
                </td>
                <td className="text-right text-slate-400 text-xs">
                  {order.inspection_date}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.orders.length > 10 && (
        <div className="p-3 text-center text-xs text-slate-400">
          Showing 10 of {formatNumber(data.order_count)} orders
        </div>
      )}
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
        <div className="skeleton h-32 w-full rounded" />
      </div>
    </div>
  );
}
