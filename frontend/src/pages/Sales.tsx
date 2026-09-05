import { useEffect, useState, useMemo } from 'react';
import { Filter, ChevronDown, ChevronUp } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, PieChart, Pie, Cell as PieCell
} from 'recharts';
import { api } from '../lib/api';
import { formatNumber, formatCurrency, formatPercent, cn } from '../lib/utils';

interface SalesData {
  sales_trend: Array<{ date: string; units: number; revenue: number }>;
  store_performance: Array<{ id: number; name: string; city: string; units_sold: number; revenue: number; products_sold: number }>;
  top_products: Array<{ id: number; name: string; category: string; total_qty: number; total_revenue: number }>;
}

export function Sales() {
  const [data, setData] = useState<SalesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [storeFilter, setStoreFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [stores, setStores] = useState<Array<{ id: number; name: string; city: string }>>([]);
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [trend, storePerf, topProds, storesData, productsData] = await Promise.all([
          api.sales(days, storeFilter ? parseInt(storeFilter) : undefined, categoryFilter || undefined),
          api.storePerformance(),
          api.topProducts(10),
          api.stores(),
          api.products(),
        ]);

        setData({
          sales_trend: trend,
          store_performance: storePerf,
          top_products: topProds,
        });
        setStores(storesData);
        const cats = [...new Set(productsData.map((p: any) => p.category))];
        setCategories(cats);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [days, storeFilter, categoryFilter]);

  const COLORS = ['#6366f1', '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Sales Analytics</h1>
        </div>
        <div className="card animate-pulse h-96"></div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">Failed to load sales data</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sales Analytics</h1>
          <p className="text-gray-500 mt-1">Track sales trends, store performance, and product rankings</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <select
            value={days}
            onChange={(e) => setDays(parseInt(e.target.value))}
            className="input w-auto"
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
          <select
            value={storeFilter}
            onChange={(e) => setStoreFilter(e.target.value)}
            className="input w-auto"
          >
            <option value="">All Stores</option>
            {stores.map((s) => (
              <option key={s.id} value={s.id}>{s.city}</option>
            ))}
          </select>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="input w-auto"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Sales Trend</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.sales_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  stroke="#9ca3af"
                  fontSize={11}
                  interval="preserveStartEnd"
                />
                <YAxis stroke="#9ca3af" fontSize={11} tickFormatter={formatNumber} />
                <Tooltip
                  formatter={(value, name) => [value != null ? (name === 'revenue' ? formatCurrency(value as number) : formatNumber(value as number)) : '', name]}
                  labelFormatter={(value) => value ? new Date(String(value)).toLocaleDateString() : ''}
                />
                <Line
                  type="monotone"
                  dataKey="revenue"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={false}
                  name="Revenue"
                />
                <Line
                  type="monotone"
                  dataKey="units"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={false}
                  name="Units"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Store Comparison</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.store_performance} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" stroke="#9ca3af" fontSize={11} tickFormatter={formatCurrency} />
                <YAxis
                  type="category"
                  dataKey="city"
                  stroke="#9ca3af"
                  fontSize={11}
                  width={120}
                  tick={{ fill: '#374151' }}
                />
                <Tooltip formatter={(value: number | undefined) => [value != null ? formatCurrency(value) : '', 'Revenue']} />
                <Bar
                  dataKey="revenue"
                  fill="#6366f1"
                  radius={[0, 4, 4, 0]}
                  maxBarSize={40}
                >
                  {data.store_performance.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Products by Revenue</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100">
                  <th className="pb-2 font-medium">Rank</th>
                  <th className="pb-2 font-medium">Product</th>
                  <th className="pb-2 font-medium">Category</th>
                  <th className="pb-2 font-medium text-right">Units</th>
                  <th className="pb-2 font-medium text-right">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {data.top_products.slice(0, 15).map((product, index) => (
                  <tr key={product.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 text-gray-500 font-medium">#{index + 1}</td>
                    <td className="py-2 font-medium text-gray-900">{product.name}</td>
                    <td className="py-2 text-gray-500">{product.category}</td>
                    <td className="py-2 text-right text-gray-700">{formatNumber(product.total_qty)}</td>
                    <td className="py-2 text-right font-medium text-gray-900">{formatCurrency(product.total_revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Revenue by Store</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.store_performance}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  dataKey="revenue"
                  nameKey="city"
                  labelLine={false}
                >
                  {data.store_performance.map((_, index) => (
                    <PieCell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [value != null ? formatCurrency(value as number) : '', 'Revenue']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-2 text-sm">
            {data.store_performance.map((store) => (
              <div key={store.id} className="flex items-center justify-between">
                <span className="text-gray-600">{store.city}</span>
                <div className="flex items-center gap-4">
                  <span className="font-medium text-gray-900">{formatCurrency(store.revenue)}</span>
                  <span className="text-gray-500">{formatNumber(store.units_sold)} units</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}