import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export function SentimentDistributionChart({ data }) {
    if (!data) return <div className="no-chart-data">No distribution data available.</div>;

    // Data format: { positive: number, neutral: number, negative: number }
    const chartData = [
        { name: 'Positive', value: data.positive, color: '#4CAF50' },
        { name: 'Neutral', value: data.neutral, color: '#FFC107' },
        { name: 'Negative', value: data.negative, color: '#f44336' },
    ].filter(item => item.value > 0);

    return (
        <div className="chart-container">
            <h4>Sentiment Distribution</h4>
            <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                    <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                    >
                        {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: '12px', background: '#fff', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                    <Legend verticalAlign="bottom" height={36} />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
}
