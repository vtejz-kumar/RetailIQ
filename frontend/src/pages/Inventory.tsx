import { useEffect, useState, useMemo } from 'react';
import { Search, Filter, ChevronDown, ChevronUp, Download } from 'lucide-react';
import { api } from '../lib/api';
import { formatNumber, formatCurrency, getRiskBadgeClass, cn } from '../lib/utils';

interface InventoryItem {
  id: number;
  snapshot_date: string;
  store_id: number;
  product_id: number;
  stock_quantity: number;
  product_name: string;
  category: string;
  price: number;
  cost: number;
  reorder_threshold: number;
  target_stock: number;
  store_name: string;
}

interface StockStatus {
  product_id: number;
  product_name: string;
  store_id: number;
  store_name: string;
  category: string;
  current_stock: number;
  avg_daily_sales: number;
  days_remaining: number | null;
  risk_level: string;
  reorder_threshold: number;
}

type MergedInventoryItem = InventoryItem & {
  avg_daily_sales: number;
  days_remaining: number | null;
  risk_level: string;
};

export function Inventory() {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [stockStatus, setStockStatus] = useState<StockStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [storeFilter, setStoreFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [stores, setStores] = useState<Array<{ id: number; name: string; city: string }>>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' }>({ key: 'risk_level', direction: 'asc' });

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [inv, risks, storesData, productsData] = await Promise.all([
          api.inventory(),
          api.risks(),
          api.stores(),
          api.products(),
        ]);
        setInventory(inv);
        setStockStatus(risks);
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
  }, []);

  const mergedData = useMemo(() => {
    const statusMap = new Map();
    stockStatus.forEach((s) => {
      statusMap.set(`${s.product_id}-${s.store_id}`, s);
    });

    return inventory.map((item): MergedInventoryItem => {
      const status = statusMap.get(`${item.product_id}-${item.store_id}`);
      return {
        ...item,
        avg_daily_sales: status?.avg_daily_sales ?? 0,
        days_remaining: status?.days_remaining ?? null,
        risk_level: status?.risk_level ?? 'UNKNOWN',
      };
    });
  }, [inventory, stockStatus]);

  const filteredData = useMemo(() => {
    return mergedData.filter((item) => {
      const matchesSearch = search === '' ||
        item.product_name.toLowerCase().includes(search.toLowerCase()) ||
        item.store_name.toLowerCase().includes(search.toLowerCase());
      const matchesStore = storeFilter === '' || item.store_id === parseInt(storeFilter);
      const matchesCategory = categoryFilter === '' || item.category === categoryFilter;
      const matchesRisk = riskFilter === '' || item.risk_level === riskFilter;
      return matchesSearch && matchesStore && matchesCategory && matchesRisk;
    }).sort((a, b) => {
      const aVal = a[sortConfig.key as keyof typeof a];
      const bVal = b[sortConfig.key as keyof typeof b];
      if (aVal === null && bVal === null) return 0;
      if (aVal === null) return 1;
      if (bVal === null) return -1;
      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [mergedData, search, storeFilter, categoryFilter, riskFilter, sortConfig]);

  const handleSort = (key: string) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const riskOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, NO_RECENT_SALES: 3, HEALTHY: 4, UNKNOWN: 5 };

  const sortedData = useMemo(() => {
    return [...filteredData].sort((a, b) => {
      const aRisk = riskOrder[a.risk_level as keyof typeof riskOrder] ?? 5;
      const bRisk = riskOrder[b.risk_level as keyof typeof riskOrder] ?? 5;
      return aRisk - bRisk;
    });
  }, [filteredData]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
        </div>
        <div className="card">
          <div className="animate-pulse space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
          <p className="text-gray-500 mt-1">Monitor stock levels, risk status, and reorder needs</p>
        </div>
      </div>

      <div className="card">
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search products or stores..."
              className="input pl-10"
            />
          </div>
          <div className="flex flex-wrap gap-3">
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
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="input w-auto"
            >
              <option value="">All Risk Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="HEALTHY">Healthy</option>
              <option value="NO_RECENT_SALES">No Recent Sales</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-100">
                {[
                  { key: 'product_name', label: 'Product' },
                  { key: 'store_name', label: 'Store' },
                  { key: 'category', label: 'Category' },
                  { key: 'stock_quantity', label: 'Stock' },
                  { key: 'avg_daily_sales', label: 'Avg Daily Sales' },
                  { key: 'days_remaining', label: 'Days Remaining' },
                  { key: 'risk_level', label: 'Risk' },
                  { key: 'reorder_threshold', label: 'Reorder At' },
                ].map((col) => (
                  <th
                    key={col.key}
                    className="pb-3 font-medium cursor-pointer hover:text-gray-700"
                    onClick={() => handleSort(col.key)}
                  >
                    <div className="flex items-center gap-1">
                      {col.label}
                      {sortConfig.key === col.key && (
                        sortConfig.direction === 'asc'
                          ? <ChevronUp className="w-4 h-4" />
                          : <ChevronDown className="w-4 h-4" />
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedData.map((item) => (
                <tr key={`${item.product_id}-${item.store_id}`} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-3 font-medium text-gray-900">{item.product_name}</td>
                  <td className="py-3 text-gray-500">{item.store_name}</td>
                  <td className="py-3 text-gray-500">{item.category}</td>
                  <td className="py-3 font-medium text-gray-900">{formatNumber(item.stock_quantity)}</td>
                  <td className="py-3 text-gray-700">{item.avg_daily_sales.toFixed(1)}/day</td>
                  <td className="py-3">
                    {item.days_remaining !== null ? (
                      <span className={cn(
                        'font-medium',
                        item.days_remaining <= 3 ? 'text-red-600' :
                        item.days_remaining <= 7 ? 'text-orange-600' :
                        item.days_remaining <= 14 ? 'text-yellow-600' :
                        'text-green-600'
                      )}>
                        {item.days_remaining.toFixed(1)} days
                      </span>
                    ) : (
                      <span className="text-gray-500">No recent sales</span>
                    )}
                  </td>
                  <td className="py-3">
                    <span className={cn('badge', getRiskBadgeClass(item.risk_level))}>
                      {item.risk_level.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3 text-gray-700">{item.reorder_threshold}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {sortedData.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No inventory items match your filters.
            </div>
          )}
        </div>

        <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
          <span>Showing {sortedData.length} of {mergedData.length} items</span>
        </div>
      </div>
    </div>
  );
}