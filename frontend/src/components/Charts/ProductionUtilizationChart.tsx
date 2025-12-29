import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ProductionUtilizationData {
  plant_name: string;
  plant_id: string;
  production_used: number;
  production_capacity: number;
  utilization_pct: number;
}

interface Props {
  data?: ProductionUtilizationData[];
}

const ProductionUtilizationChart = ({ data }: Props) => {
  if (!data || data.length === 0) {
    return <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>No data available</div>;
  }

  const chartData = data.map(item => ({
    name: item.plant_name.replace(' Plant', '').replace(' Clinker', ''),
    used: item.production_used,
    capacity: item.production_capacity,
    utilization: item.utilization_pct * 100,
  }));

  const formatTonnes = (value: number) => {
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{
          background: 'white',
          padding: '12px',
          border: '1px solid #d9d9d9',
          borderRadius: '6px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
        }}>
          <p style={{ margin: 0, fontWeight: 600 }}>{label}</p>
          <p style={{ margin: '4px 0', color: '#1f4e79' }}>
            Used: {formatTonnes(data.used)} tonnes
          </p>
          <p style={{ margin: '4px 0', color: '#2e7d32' }}>
            Capacity: {formatTonnes(data.capacity)} tonnes
          </p>
          <p style={{ margin: '4px 0', color: '#f57c00' }}>
            Utilization: {data.utilization.toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis 
          dataKey="name" 
          tick={{ fontSize: 12 }}
          interval={0}
          angle={-45}
          textAnchor="end"
          height={80}
        />
        <YAxis 
          tick={{ fontSize: 12 }}
          tickFormatter={formatTonnes}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Bar 
          dataKey="used" 
          name="Production Used" 
          fill="#1f4e79" 
          radius={[2, 2, 0, 0]}
        />
        <Bar 
          dataKey="capacity" 
          name="Total Capacity" 
          fill="#e3f2fd" 
          radius={[2, 2, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default ProductionUtilizationChart;