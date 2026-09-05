import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Copilot } from './pages/Copilot';
import { Inventory } from './pages/Inventory';
import { Sales } from './pages/Sales';
import { Alerts } from './pages/Alerts';
import { Recommendations } from './pages/Recommendations';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="copilot" element={<Copilot />} />
          <Route path="inventory" element={<Inventory />} />
          <Route path="sales" element={<Sales />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="recommendations" element={<Recommendations />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}