import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  DollarSign,
  Package,
  Box,
  AlertTriangle,
  TrendingUp,
  Store,
  ArrowUpRight,
  ArrowDownRight,
  ChevronRight,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, PieChart, Pie, Cell as PieCell } from 'recharts';
import { api } from '../lib/api';
import { formatCurrency, formatNumber, formatPercent, getRiskBadgeClass, cn } from '../lib/utils';

interface DashboardData {
  kpis: {
    total_revenue: number;
    total_units_sold: number;
    inventory_value: number;
    low_stock_count: number;
    overstock_count: number;
    attention_count: number;
  };
  sales_trend: Array<{ date: string; units: number; revenue: number }>;
  store_performance: Array<{ id: number; name: string; city: string; units_sold: number; revenue: number }>;
  top_products: Array<{ id: number; name: string; category: string; total_qty: number; total_revenue: number }>;
  inventory_health: Array<{ risk_level: string; count: number }>;
  anomaly_summary: { spike_count: number; drop_count: number; total: number };
}

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const result = await api.dashboard();
        setData(result);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="card text-center py-12">
        <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h2 className="text-lg font-medium text-gray-900 mb-2">Unable to load dashboard</h2>
        <p className="text-gray-500">{error || 'Unknown error'}</p>
      </div>
    );
  }

  const kpiCards = [
    {
      title: 'Total Revenue',
      value: formatCurrency(data.kpis.total_revenue),
      icon: DollarSign,
      iconBg: 'bg-indigo-100 text-indigo-600',
      trend: '+12.5%',
      trendUp: true,
    },
    {
      title: 'Units Sold',
      value: formatNumber(data.kpis.total_units_sold),
      icon: Package,
      iconBg: 'bg-blue-100 text-blue-600',
      trend: '+8.2%',
      trendUp: true,
    },
    {
      title: 'Inventory Value',
      value: formatCurrency(data.kpis.inventory_value),
      icon: Box,
      iconBg: 'bg-green-100 text-green-600',
      trend: '-3.1%',
      trendUp: false,
    },
    {
      title: 'Low Stock',
      value: data.kpis.low_stock_count.toString(),
      icon: AlertTriangle,
      iconBg: 'bg-red-100 text-red-600',
      trend: 'Critical',
      trendUp: false,
    },
    {
      title: 'Overstock',
      value: data.kpis.overstock_count.toString(),
      icon: Package,
      iconBg: 'bg-orange-100 text-orange-600',
      trend: 'Review needed',
      trendUp: false,
    },
    {
      title: 'Needs Attention',
      value: data.kpis.attention_count.toString(),
      icon: AlertTriangle,
      iconBg: 'bg-purple-100 text-purple-600',
      trend: 'View details',
      trendUp: false,
    },
  ];

  const COLORS = ['#6366f1', '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Overview of your retail operations</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {kpiCards.map((kpi, index) => (
          <Link
            key={kpi.title}
            to={kpi.title === 'Low Stock' ? '/inventory?risk=CRITICAL' : 
               kpi.title === 'Overstock' ? '/inventory?risk=OVERSTOCK' : 
               kpi.title === 'Needs Attention' ? '/alerts' : '#'}
            className="card hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">{kpi.title}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{kpi.value}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className={cn('text-sm font-medium', kpi.trendUp ? 'text-green-600' : 'text-red-600')}>
                    {kpi.trendUp ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                    {kpi.trend}
                  </span>
                </div>
              </div>
              <div className={cn('p-3 rounded-xl', kpi.iconBg)}>
                <kpi.icon className="w-6 h-6" aria-hidden="true" />
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Sales Trend (Last 30 Days)</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.sales_trend.slice(-30)}>
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
                  formatter={(value, name) => [value != null ? formatNumber(value as number) : '', name === 'revenue' ? 'Revenue' : 'Units']}
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
                  yAxisId="right"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Store Performance</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.store_performance} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" stroke="#9ca3af" fontSize={11} tickFormatter={formatNumber} />
                <YAxis
                  type="category"
                  dataKey="city"
                  stroke="#9ca3af"
                  fontSize={11}
                  width={120}
                  tick={{ fill: '#374151' }}
                />
                <Tooltip formatter={(value) => [value != null ? formatCurrency(value as number) : '', 'Revenue']} />
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Products by Revenue</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100">
                  <th className="pb-2 font-medium">Product</th>
                  <th className="pb-2 font-medium">Category</th>
                  <th className="pb-2 font-medium text-right">Units Sold</th>
                  <th className="pb-2 font-medium text-right">Revenue</th>
                </tr>
              </thead>
              <tbody>
                {data.top_products.slice(0, 10).map((product, index) => (
                  <tr key={product.id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-3 font-medium text-gray-900">{product.name}</td>
                    <td className="py-3 text-gray-500">{product.category}</td>
                    <td className="py-3 text-right text-gray-700">{formatNumber(product.total_qty)}</td>
                    <td className="py-3 text-right font-medium text-gray-900">{formatCurrency(product.total_revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Inventory Health</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.inventory_health}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  dataKey="count"
                  nameKey="risk_level"
                  labelLine={false}
                >
                  {data.inventory_health.map((entry, index) => (
                    <PieCell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [value != null ? String(value) : '', 'Items']} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
            {data.inventory_health.map((entry) => (
              <div key={entry.risk_level} className="flex items-center gap-2">
                <span className={cn('badge', getRiskBadgeClass(entry.risk_level))}>
                  {entry.risk_level.replace('_', ' ')}
                </span>
                <span className="font-medium text-gray-900">{entry.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Attention Required</h2>
          <Link to="/alerts" className="text-sm text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1">
            View all
            <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-red-50 rounded-lg border border-red-100">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <span className="font-medium text-red-800">Critical Stock-Out Risk</span>
            </div>
            <p className="text-3xl font-bold text-red-700">{data.kpis.low_stock_count}</p>
            <p className="text-sm text-red-600 mt-1">Products need immediate reorder</p>
          </div>
          <div className="p-4 bg-orange-50 rounded-lg border border-orange-100">
            <div className="flex items-center gap-2 mb-2">
              <Package className="w-5 h-5 text-orange-600" />
              <span className="font-medium text-orange-800">Overstocked Items</span>
            </div>
            <p className="text-3xl font-bold text-orange-700">{data.kpis.overstock_count}</p>
            <p className="text-sm text-orange-600 mt-1">Slow-moving inventory</p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg border border-purple-100">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-purple-600" />
              <span className="font-medium text-purple-800">Sales Anomalies</span>
            </div>
            <p className="text-3xl font-bold text-purple-700">{data.anomaly_summary.total}</p>
            <p className="text-sm text-purple-600 mt-1">
              {data.anomaly_summary.spike_count} spikes, {data.anomaly_summary.drop_count} drops
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}