import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: unknown[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number): string {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
  return num.toLocaleString();
}

export function formatCurrency(num: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(num);
}

export function formatPercent(num: number): string {
  return `${num >= 0 ? '+' : ''}${num.toFixed(1)}%`;
}

export function getRiskBadgeClass(risk: string): string {
  switch (risk) {
    case 'CRITICAL': return 'badge-critical';
    case 'HIGH': return 'badge-high';
    case 'MEDIUM': return 'badge-medium';
    case 'HEALTHY': return 'badge-healthy';
    case 'NO_RECENT_SALES': return 'badge-no-sales';
    default: return 'badge-no-sales';
  }
}

export function getPriorityBadgeClass(priority: string): string {
  switch (priority) {
    case 'CRITICAL': return 'badge-critical';
    case 'HIGH': return 'badge-high';
    case 'MEDIUM': return 'badge-medium';
    case 'LOW': return 'badge-healthy';
    default: return 'badge-no-sales';
  }
}

export function getActionColor(action: string): string {
  switch (action) {
    case 'REORDER': return 'text-red-600 bg-red-50';
    case 'TRANSFER': return 'text-blue-600 bg-blue-50';
    case 'PROMOTE': return 'text-green-600 bg-green-50';
    case 'INVESTIGATE': return 'text-purple-600 bg-purple-50';
    case 'MONITOR': return 'text-gray-600 bg-gray-50';
    default: return 'text-gray-600 bg-gray-50';
  }
}