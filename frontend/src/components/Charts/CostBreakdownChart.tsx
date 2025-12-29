import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface CostBreakdownData {
  production_cost: number;
  transport_cost: number;
  fixed_trip_cost: number;
  holding_cost: number;
  penalty_cost: number;
}

interface Props {
  data?: CostBreakdownData;
}

const COLORS = ['#1f4e79', '#2e7d32', '#f57c00', '#9c27b0', '#d32f2f'];

const CostBreakdownChart = ({ data }: Props) => {
  if (!data) {
    return <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>No data available</div>;
  }

  const chartData = [
    { name: 'Production', value: data.production_cost, color: COLORS[0] },
    { name: 'Transport', value: data.transport_cost, color: COLORS[1] },
    { name: 'Fixed Trips', value: data.fixed_trip_cost, color: COLORS[2] },
    { name: 'Holding', value: data.holding_cost, color: COLORS[3] },
    { name: 'Penalty', value: data.penalty_cost, color: COLORS[4] },
  ].filter(item => item.value > 0);

  const formatCurrency = (value: number) => {
    if (value >= 10000000) {
      return `₹${(value / 10000000).toFixed(1)} Cr`;
    } else if (value >= 100000) {
      return `₹${(value / 100000).toFixed(1)} L`;
    } else if (value >= 1000) {
      return `₹${(value / 1000).toFixed(1)} K`;
    }
    return `₹${value.toFixed(0)}`;
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div style={{
          background: 'white',
          padding: '12px',
          border: '1px solid #d9d9d9',
          borderRadius: '6px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
        }}>
          <p style={{ margin: 0, fontWeight: 600 }}>{data.name}</p>
          <p style={{ margin: 0, color: data.payload.color }}>
            {formatCurrency(data.value)}
          </p>
          <p style={{ margin: 0, fontSize: '0.9rem', color: '#666' }}>
            {((data.value / chartData.reduce((sum, item) => sum + item.value, 0)) * 100).toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={120}
          paddingAngle={2}
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend 
          formatter={(value, entry: any) => (
            <span style={{ color: entry.color, fontSize: '0.9rem' }}>
              {value}: {formatCurrency(entry.payload.value)}
            </span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default CostBreakdownChart;