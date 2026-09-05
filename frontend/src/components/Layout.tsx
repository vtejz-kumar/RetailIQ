import { type ReactNode } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import {
  LayoutDashboard,
  Bot,
  PackageSearch,
  TrendingUp,
  AlertTriangle,
  ListChecks,
  Settings,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'AI Copilot', href: '/copilot', icon: Bot },
  { name: 'Inventory', href: '/inventory', icon: PackageSearch },
  { name: 'Sales', href: '/sales', icon: TrendingUp },
  { name: 'Alerts', href: '/alerts', icon: AlertTriangle },
  { name: 'Recommendations', href: '/recommendations', icon: ListChecks },
];

export function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <NavLink
                to="/"
                className="flex items-center gap-2 text-xl font-bold text-indigo-600"
              >
                <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">R</span>
                </div>
                <span>RetailIQ</span>
              </NavLink>
              <nav className="hidden md:flex items-center gap-1" aria-label="Main navigation">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href ||
                    (item.href !== '/' && location.pathname.startsWith(item.href));
                  return (
                    <NavLink
                      key={item.name}
                      to={item.href}
                      className={cn(
                        'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-indigo-50 text-indigo-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      )}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <item.icon className="w-5 h-5" aria-hidden="true" />
                      {item.name}
                    </NavLink>
                  );
                })}
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500 hidden sm:block">AI Sales & Inventory Copilot</span>
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  );
}