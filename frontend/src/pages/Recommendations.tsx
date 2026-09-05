import { useEffect, useState } from 'react';
import { AlertTriangle, TrendingUp, TrendingDown, Eye, Package, Lightbulb, ClipboardList, ExternalLink } from 'lucide-react';
import { api } from '../lib/api';
import { formatNumber, formatPercent, getPriorityBadgeClass, cn, getActionColor } from '../lib/utils';

interface Recommendation {
  product_id: number;
  product_name: string;
  store_id: number;
  store_name: string;
  action: string;
  priority: string;
  reason: string;
  evidence: {
    current_stock?: number;
    avg_daily_sales?: number;
    days_remaining?: number | null;
    risk_level?: string;
    reorder_threshold?: number;
    days_inventory?: number;
    recent_sales_7d?: number;
    anomaly_type?: string;
    historical_avg_daily?: number;
    recent_avg_daily?: number;
    pct_change?: number;
  };
  assumptions: string[];
}

export function Recommendations() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const data = await api.recommendations();
        setRecommendations(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const groupedByPriority = {
    CRITICAL: recommendations.filter(r => r.priority === 'CRITICAL'),
    HIGH: recommendations.filter(r => r.priority === 'HIGH'),
    MEDIUM: recommendations.filter(r => r.priority === 'MEDIUM'),
    LOW: recommendations.filter(r => r.priority === 'LOW'),
  };

  const formatNum = (v: string) => formatNumber(parseFloat(v) || 0);
  const formatPct = (v: string) => formatPercent(parseFloat(v) || 0);

  const priorityOrder = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const;
  const priorityIcons = {
    CRITICAL: AlertTriangle,
    HIGH: AlertTriangle,
    MEDIUM: TrendingUp,
    LOW: Lightbulb,
  };
  const priorityColors = {
    CRITICAL: 'red',
    HIGH: 'orange',
    MEDIUM: 'yellow',
    LOW: 'gray',
  };

  const toggleExpand = (id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const isExpanded = (id: string) => expandedIds.has(id);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Recommendations</h1>
          <p className="text-gray-500 mt-1">Actionable insights prioritized by urgency</p>
        </div>
      </div>

      {priorityOrder.map((priority) => {
        const items = groupedByPriority[priority];
        if (items.length === 0) return null;

        const PriorityIcon = priorityIcons[priority];
        const color = priorityColors[priority];

        return (
          <div key={priority} className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <PriorityIcon className={cn('w-6 h-6', `text-${color}-600`)} />
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{priority} Priority</h2>
                  <p className="text-sm text-gray-500">{items.length} recommendation{items.length !== 1 ? 's' : ''}</p>
                </div>
              </div>
              <span className={cn('badge', getPriorityBadgeClass(priority))}>{priority}</span>
            </div>

            <div className="space-y-3">
              {items.map((rec) => {
                const recId = `${rec.product_id}-${rec.store_id}-${rec.action}`;
                const expanded = isExpanded(recId);

                return (
                  <div key={recId} className="border border-gray-100 rounded-lg overflow-hidden">
                    <button
                      onClick={() => toggleExpand(recId)}
                      className="w-full p-4 text-left hover:bg-gray-50 transition-colors flex items-start justify-between gap-4"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 flex-wrap mb-2">
                          <span className="font-medium text-gray-900 truncate">{rec.product_name}</span>
                          <span className={cn('px-2 py-0.5 rounded text-xs font-medium', getActionColor(rec.action))}>
                            {rec.action}
                          </span>
                          <span className={cn('badge', getPriorityBadgeClass(rec.priority))}>{rec.priority}</span>
                          <span className="text-sm text-gray-500">{rec.store_name}</span>
                        </div>
                        <p className="text-sm text-gray-600 line-clamp-2">{rec.reason}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <ExternalLink className="text-gray-400 hover:text-gray-600 p-1" />
                        <Eye
                          className={cn('w-5 h-5 text-gray-400 transition-transform', expanded && 'rotate-180')}
                          aria-hidden="true"
                        />
                      </div>
                    </button>

                    {expanded && (
                      <div className="bg-gray-50 border-t border-gray-100 p-4 space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <EvidenceCard title="Current Stock" value={rec.evidence.current_stock?.toString() ?? 'N/A'} format={formatNum} icon={Package} />
                          {rec.evidence.avg_daily_sales !== undefined && (
                            <EvidenceCard title="Avg Daily Sales" value={rec.evidence.avg_daily_sales.toFixed(1)} suffix="/day" icon={TrendingUp} />
                          )}
                          {rec.evidence.days_remaining !== undefined && rec.evidence.days_remaining !== null && (
                            <EvidenceCard title="Days Remaining" value={rec.evidence.days_remaining.toFixed(1)} suffix=" days" icon={AlertTriangle} />
                          )}
                          {rec.evidence.days_inventory !== undefined && (
                            <EvidenceCard title="Days Inventory" value={rec.evidence.days_inventory.toFixed(0)} suffix=" days" icon={Package} />
                          )}
                          {rec.evidence.recent_sales_7d !== undefined && (
                            <EvidenceCard title="Recent Sales (7d)" value={rec.evidence.recent_sales_7d.toString()} format={formatNum} icon={ClipboardList} />
                          )}
                          {rec.evidence.pct_change !== undefined && (
                            <EvidenceCard title="Sales Change" value={formatPct(rec.evidence.pct_change.toString())} icon={rec.evidence.pct_change > 0 ? TrendingUp : TrendingDown} />
                          )}
                        </div>

                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Reasoning</h4>
                          <p className="text-sm text-gray-600">{rec.reason}</p>
                        </div>

                        {rec.assumptions && rec.assumptions.length > 0 && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">Assumptions</h4>
                            <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                              {rec.assumptions.map((assumption, i) => (
                                <li key={i}>{assumption}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      {recommendations.length === 0 && (
        <div className="card text-center py-12">
          <Lightbulb className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-gray-900 mb-2">No recommendations at this time</h2>
          <p className="text-gray-500">All inventory levels and sales patterns appear normal.</p>
        </div>
      )}
    </div>
  );
}

function EvidenceCard({ title, value, suffix = '', format, icon: Icon }: { 
  title: string; 
  value: string; 
  suffix?: string; 
  format?: (v: string) => string; 
  icon: React.FC<{ className?: string }> 
}) {
  const displayValue = format ? format(value) : value;
  return (
    <div className="p-3 bg-white rounded-lg border border-gray-100">
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
        <Icon className="w-4 h-4" />
        <span>{title}</span>
      </div>
      <p className="font-semibold text-gray-900 text-lg">{displayValue}{suffix}</p>
    </div>
  );
}