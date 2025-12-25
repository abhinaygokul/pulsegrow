import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export function SentimentTrendChart({ data }) {
    if (!data || data.length === 0) return <div className="no-chart-data">No trend data available.</div>;

    return (
        <div className="chart-container">
            <h4>Sentiment Trend (Over Time)</h4>
            <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorPos" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#4CAF50" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#4CAF50" stopOpacity={0.1} />
                        </linearGradient>
                        <linearGradient id="colorNeu" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#FFC107" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#FFC107" stopOpacity={0.1} />
                        </linearGradient>
                        <linearGradient id="colorNeg" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f44336" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#f44336" stopOpacity={0.1} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="title" hide={true} />
                    <YAxis unit="%" />
                    <Tooltip
                        contentStyle={{ borderRadius: '12px', background: '#fff', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                        formatter={(value, name) => [`${value}%`, name]}
                    />
                    <Legend />
                    <Area type="monotone" dataKey="negative" stackId="1" stroke="#f44336" fill="url(#colorNeg)" name="Negative" />
                    <Area type="monotone" dataKey="neutral" stackId="1" stroke="#FFC107" fill="url(#colorNeu)" name="Neutral" />
                    <Area type="monotone" dataKey="positive" stackId="1" stroke="#4CAF50" fill="url(#colorPos)" name="Positive" />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
