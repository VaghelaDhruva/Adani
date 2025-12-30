import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import Dashboard from './pages/Dashboard';
import DataHealth from './pages/DataHealth';
import DataValidation from './pages/DataValidation';
import OptimizationConsole from './pages/OptimizationConsole';
import Results from './pages/Results';
import ScenarioComparison from './pages/ScenarioComparison';
import SystemHealth from './pages/SystemHealth';

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
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/data-health" element={<DataHealth />} />
            <Route path="/data-validation" element={<DataValidation />} />
            <Route path="/optimization" element={<OptimizationConsole />} />
            <Route path="/results" element={<Results />} />
            <Route path="/scenarios" element={<ScenarioComparison />} />
            <Route path="/system" element={<SystemHealth />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;