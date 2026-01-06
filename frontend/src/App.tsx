import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import Dashboard from './pages/Dashboard';
import TransportModeSelection from './pages/TransportModeSelection';
// New Clinker Workflow Pages
import OrderCreation from './pages/clinker/OrderCreation';
import InventoryCheck from './pages/clinker/InventoryCheck';
import DispatchPlanning from './pages/clinker/DispatchPlanning';
import LoadingExecution from './pages/clinker/LoadingExecution';
import InTransitTracking from './pages/clinker/InTransitTracking';
import DeliveryGRN from './pages/clinker/DeliveryGRN';
import BillingCosting from './pages/clinker/BillingCosting';
import DemandApproval from './pages/clinker/DemandApproval';

const { Content } = Layout;

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout>
        <Header />
        <Content style={{ 
          margin: '24px 16px', 
          padding: 24, 
          background: 'transparent', 
          borderRadius: 16,
          minHeight: 'calc(100vh - 112px)' 
        }}>
          <Routes>
            {/* Core Dashboards - Keep These */}
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/transport" element={<TransportModeSelection />} />
            
            {/* New Clinker Workflow Routes */}
            <Route path="/clinker/orders" element={<OrderCreation />} />
            <Route path="/clinker/inventory" element={<InventoryCheck />} />
            <Route path="/clinker/dispatch" element={<DispatchPlanning />} />
            <Route path="/clinker/loading" element={<LoadingExecution />} />
            <Route path="/clinker/tracking" element={<InTransitTracking />} />
            <Route path="/clinker/delivery" element={<DeliveryGRN />} />
            <Route path="/clinker/billing" element={<BillingCosting />} />
            <Route path="/clinker/approval" element={<DemandApproval />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;