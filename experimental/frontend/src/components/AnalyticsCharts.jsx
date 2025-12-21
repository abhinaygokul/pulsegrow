import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import './AnalyticsCharts.css';

export function AnalyticsCharts({ videos }) {
    if (!videos || videos.length === 0) return null;

    // Filter for analyzed videos ONLY
    const analyzedVideos = videos.filter(v => v.analysis_status === 'completed');

    if (analyzedVideos.length === 0) {
        return (
            <div className="charts-container empty-state">
                <div className="empty-charts-message">
                    <p>No analysis data yet. Analyze some videos below to see trends.</p>
                </div>
            </div>
        );
    }

    // Prepare Data for Trend Chart (Sentiment over Time)
    const trendData = analyzedVideos
        .sort((a, b) => new Date(a.published_at) - new Date(b.published_at))
        .map(v => ({
            name: new Date(v.published_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
            sentiment: v.sentiment_score,
            title: v.title
        }));

    // Prepare Data for Distribution (Pie Chart)
    let positive = 0, neutral = 0, negative = 0;
    analyzedVideos.forEach(v => {
        if (v.sentiment_score > 0.05) positive++;
        else if (v.sentiment_score < -0.05) negative++;
        else neutral++;
    });

    const pieData = [
        { name: 'Positive', value: positive, color: '#4ade80' },
        { name: 'Neutral', value: neutral, color: '#94a3b8' },
        { name: 'Negative', value: negative, color: '#f87171' },
    ];

    return (
        <div className="charts-container">
            <div className="chart-card">
                <h3>Sentiment Trend</h3>
                <div className="chart-wrapper">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={trendData}>
                            <defs>
                                <linearGradient id="colorSentiment" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="var(--md-sys-color-primary)" stopOpacity={0.8} />
                                    <stop offset="95%" stopColor="var(--md-sys-color-primary)" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--md-sys-color-outline)" opacity={0.3} />
                            <XAxis dataKey="name" stroke="var(--color-text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                            <YAxis stroke="var(--color-text-muted)" fontSize={12} tickLine={false} axisLine={false} domain={[-1, 1]} />
                            <Tooltip
                                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: 'var(--shadow-md)' }}
                            />
                            <Area type="monotone" dataKey="sentiment" stroke="var(--md-sys-color-primary)" fillOpacity={1} fill="url(#colorSentiment)" strokeWidth={3} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="chart-card">
                <h3>Sentiment Distribution</h3>
                <div className="chart-wrapper">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={pieData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                                stroke="none"
                            >
                                {pieData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: 'var(--shadow-md)' }} />
                            <Legend verticalAlign="bottom" height={36} iconType="circle" />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
