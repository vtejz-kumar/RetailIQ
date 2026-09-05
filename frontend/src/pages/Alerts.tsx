import { useEffect, useState } from 'react';
import { AlertTriangle, Package, TrendingUp, TrendingDown, ExternalLink } from 'lucide-react';
import { api } from '../lib/api';
import { formatNumber, formatCurrency, formatPercent, getRiskBadgeClass, cn } from '../lib/utils';

interface AlertItem {
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

interface OverstockItem {
  product_id: number;
  product_name: string;
  store_id: number;
  store_name: string;
  category: string;
  current_stock: number;
  avg_daily_sales: number;
  days_inventory: number;
  recent_sales_7d: number;
  reason: string;
  reorder_threshold: number;
}

interface AnomalyItem {
  product_id: number;
  product_name: string;
  store_id: number;
  store_name: string;
  category: string;
  anomaly_type: string;
  historical_avg: number;
  recent_avg: number;
  pct_change: number;
  recent_sales_7d: number;
  historical_sales_7d: number;
}

export function Alerts() {
  const [stockoutAlerts, setStockoutAlerts] = useState<AlertItem[]>([]);
  const [overstockAlerts, setOverstockAlerts] = useState<OverstockItem[]>([]);
  const [anomalyAlerts, setAnomalyAlerts] = useState<AnomalyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'stockout' | 'overstock' | 'anomalies'>('stockout');

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [risks, overstock, anomalies] = await Promise.all([
          api.risks(),
          api.overstock(),
          api.anomalies(),
        ]);
        setStockoutAlerts(risks);
        setOverstockAlerts(overstock);
        setAnomalyAlerts(anomalies);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const criticalStockout = stockoutAlerts.filter(a => a.risk_level === 'CRITICAL');
  const highStockout = stockoutAlerts.filter(a => a.risk_level === 'HIGH');
  const spikeAnomalies = anomalyAlerts.filter(a => a.anomaly_type === 'SPIKE');
  const dropAnomalies = anomalyAlerts.filter(a => a.anomaly_type === 'DROP');

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
        </div>
        <div className="card animate-pulse h-96"></div>
      </div>
    );
  }

  const tabs = [
    { id: 'stockout', label: 'Stock-Out Risk', count: criticalStockout.length + highStockout.length, icon: AlertTriangle, color: 'text-red-600' },
    { id: 'overstock', label: 'Overstock', count: overstockAlerts.length, icon: Package, color: 'text-orange-600' },
    { id: 'anomalies', label: 'Sales Anomalies', count: anomalyAlerts.length, icon: TrendingUp, color: 'text-purple-600' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          <p className="text-gray-500 mt-1">Monitor critical issues requiring attention</p>
        </div>
      </div>

      <div className="card">
        <div className="border-b border-gray-100 mb-6">
          <nav className="flex gap-1" aria-label="Alert categories">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={cn(
                  'flex items-center gap-2 px-4 py-3 text-sm font-medium rounded-t-lg transition-colors border-b-2 -mb-px',
                  activeTab === tab.id
                    ? 'border-indigo-600 text-indigo-600 bg-indigo-50'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                )}
              >
                <tab.icon className={cn('w-5 h-5', tab.color)} />
                {tab.label}
                <span className={cn('badge', activeTab === tab.id ? 'bg-indigo-100 text-indigo-700' : 'bg-gray-100 text-gray-600')}>
                  {tab.count}
                </span>
              </button>
            ))}
          </nav>
        </div>

        {activeTab === 'stockout' && (
          <div className="space-y-6">
            {criticalStockout.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-red-700 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  Critical Risk ({criticalStockout.length})
                </h3>
                <div className="space-y-2">
                  {criticalStockout.slice(0, 20).map((alert) => (
                    <StockoutAlertCard key={`${alert.product_id}-${alert.store_id}`} alert={alert} />
                  ))}
                </div>
              </div>
            )}
            {highStockout.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-orange-700 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  High Risk ({highStockout.length})
                </h3>
                <div className="space-y-2">
                  {highStockout.slice(0, 20).map((alert) => (
                    <StockoutAlertCard key={`${alert.product_id}-${alert.store_id}`} alert={alert} />
                  ))}
                </div>
              </div>
            )}
            {criticalStockout.length === 0 && highStockout.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                No stock-out alerts. All products have healthy inventory levels.
              </div>
            )}
          </div>
        )}

        {activeTab === 'overstock' && (
          <div>
            <h3 className="text-lg font-semibold text-orange-700 mb-3 flex items-center gap-2">
              <Package className="w-5 h-5" />
              Overstocked Items ({overstockAlerts.length})
            </h3>
            {overstockAlerts.length > 0 ? (
              <div className="space-y-2">
                {overstockAlerts.slice(0, 20).map((alert) => (
                  <OverstockAlertCard key={`${alert.product_id}-${alert.store_id}`} alert={alert} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                No overstock alerts. Inventory levels are well-balanced.
              </div>
            )}
          </div>
        )}

        {activeTab === 'anomalies' && (
          <div className="space-y-6">
            {spikeAnomalies.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-green-700 mb-3 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Sales Spikes ({spikeAnomalies.length})
                </h3>
                <div className="space-y-2">
                  {spikeAnomalies.slice(0, 20).map((anomaly) => (
                    <AnomalyAlertCard key={`${anomaly.product_id}-${anomaly.store_id}`} anomaly={anomaly} />
                  ))}
                </div>
              </div>
            )}
            {dropAnomalies.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-red-700 mb-3 flex items-center gap-2">
                  <TrendingDown className="w-5 h-5" />
                  Sales Drops ({dropAnomalies.length})
                </h3>
                <div className="space-y-2">
                  {dropAnomalies.slice(0, 20).map((anomaly) => (
                    <AnomalyAlertCard key={`${anomaly.product_id}-${anomaly.store_id}`} anomaly={anomaly} />
                  ))}
                </div>
              </div>
            )}
            {spikeAnomalies.length === 0 && dropAnomalies.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                No sales anomalies detected. Sales patterns are stable.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StockoutAlertCard({ alert }: { alert: AlertItem }) {
  return (
    <div className="p-4 bg-red-50 border border-red-100 rounded-lg">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="font-medium text-gray-900">{alert.product_name}</span>
            <span className={cn('badge', getRiskBadgeClass(alert.risk_level))}>
              {alert.risk_level}
            </span>
            <span className="text-sm text-gray-500">{alert.store_name}</span>
            <span className="text-sm text-gray-400">{alert.category}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Current Stock</span>
              <p className="font-medium text-gray-900">{formatNumber(alert.current_stock)}</p>
            </div>
            <div>
              <span className="text-gray-500">Avg Daily Sales</span>
              <p className="font-medium text-gray-900">{alert.avg_daily_sales.toFixed(1)}/day</p>
            </div>
            <div>
              <span className="text-gray-500">Days Remaining</span>
              <p className="font-medium text-red-600">
                {alert.days_remaining !== null ? alert.days_remaining.toFixed(1) : 'N/A'} days
              </p>
            </div>
            <div>
              <span className="text-gray-500">Reorder At</span>
              <p className="font-medium text-gray-900">{alert.reorder_threshold}</p>
            </div>
          </div>
        </div>
        <ExternalLink className="text-gray-400 hover:text-gray-600" />
      </div>
    </div>
  );
}

function OverstockAlertCard({ alert }: { alert: OverstockItem }) {
  return (
    <div className="p-4 bg-orange-50 border border-orange-100 rounded-lg">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="font-medium text-gray-900">{alert.product_name}</span>
            <span className="badge badge-high">OVERSTOCK</span>
            <span className="text-sm text-gray-500">{alert.store_name}</span>
            <span className="text-sm text-gray-400">{alert.category}</span>
          </div>
          <p className="text-sm text-gray-600 mb-3">{alert.reason}</p>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Stock</span>
              <p className="font-medium text-gray-900">{formatNumber(alert.current_stock)}</p>
            </div>
            <div>
              <span className="text-gray-500">Avg Daily</span>
              <p className="font-medium text-gray-900">{alert.avg_daily_sales.toFixed(2)}/day</p>
            </div>
            <div>
              <span className="text-gray-500">Days Inventory</span>
              <p className="font-medium text-orange-600">{alert.days_inventory.toFixed(0)}</p>
            </div>
            <div>
              <span className="text-gray-500">Recent (7d)</span>
              <p className="font-medium text-gray-900">{alert.recent_sales_7d}</p>
            </div>
            <div>
              <span className="text-gray-500">Reorder At</span>
              <p className="font-medium text-gray-900">{alert.reorder_threshold}</p>
            </div>
          </div>
        </div>
        <ExternalLink className="text-gray-400 hover:text-gray-600" />
      </div>
    </div>
  );
}

function AnomalyAlertCard({ anomaly }: { anomaly: AnomalyItem }) {
  const isSpike = anomaly.anomaly_type === 'SPIKE';
  return (
    <div className={cn('p-4 rounded-lg', isSpike ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100')}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="font-medium text-gray-900">{anomaly.product_name}</span>
            <span className={cn('badge', isSpike ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700')}>
              {anomaly.anomaly_type}
            </span>
            <span className="text-sm text-gray-500">{anomaly.store_name}</span>
            <span className="text-sm text-gray-400">{anomaly.category}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Historical Avg</span>
              <p className="font-medium text-gray-900">{anomaly.historical_avg.toFixed(1)}/day</p>
            </div>
            <div>
              <span className="text-gray-500">Recent Avg</span>
              <p className="font-medium text-gray-900">{anomaly.recent_avg.toFixed(1)}/day</p>
            </div>
            <div>
              <span className="text-gray-500">Change</span>
              <p className={cn('font-medium', isSpike ? 'text-green-600' : 'text-red-600')}>
                {formatPercent(anomaly.pct_change)}
              </p>
            </div>
            <div>
              <span className="text-gray-500">Recent (7d)</span>
              <p className="font-medium text-gray-900">{anomaly.recent_sales_7d}</p>
            </div>
            <div>
              <span className="text-gray-500">Historical (7d)</span>
              <p className="font-medium text-gray-900">{anomaly.historical_sales_7d}</p>
            </div>
          </div>
        </div>
        <ExternalLink className="text-gray-400 hover:text-gray-600" />
      </div>
    </div>
  );
}