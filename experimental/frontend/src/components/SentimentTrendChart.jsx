import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export function SentimentTrendChart({ data }) {
    if (!data || data.length === 0) return <div className="no-chart-data">No trend data available.</div>;

    // Data expected format: { video_title: string, score: number, date: string }

    return (
        <div className="chart-container">
            <h4>Sentiment Trend</h4>
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="title" hide={true} /> {/* Hide labels if too long */}
                    <YAxis domain={[-1, 1]} />
                    <Tooltip contentStyle={{ borderRadius: '12px', background: '#fff', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                    <Legend />
                    <Line type="monotone" dataKey="score" stroke="#8884d8" name="Sentiment Score" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 8 }} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
