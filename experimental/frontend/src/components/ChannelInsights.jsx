import React, { useMemo } from 'react';
import './ChannelInsights.css';
import { SentimentTrendChart } from './SentimentTrendChart';
import { SentimentDistributionChart } from './SentimentDistributionChart';

export function ChannelInsights({ insights, videos }) {
    if (!insights) return null;

    // Calculate Trend Data from Videos for the Chart
    const trendData = useMemo(() => {
        if (!videos || videos.length === 0) return [];
        // Sort by date ascending for the line chart
        const sorted = [...videos].sort((a, b) => new Date(a.published_at) - new Date(b.published_at));
        return sorted.map(v => ({
            title: v.title,
            score: v.score || 0,
            date: new Date(v.published_at).toLocaleDateString()
        }));
    }, [videos]);

    // Calculate Distribution Data from Videos if not in insights
    const distributionData = useMemo(() => {
        if (!videos || videos.length === 0) return { positive: 0, neutral: 0, negative: 0 };
        let pos = 0, neu = 0, neg = 0;
        videos.forEach(v => {
            if (v.score >= 0.05) pos++;
            else if (v.score <= -0.05) neg++;
            else neu++;
        });
        return { positive: pos, neutral: neu, negative: neg };
    }, [videos]);


    return (
        <div className="channel-insights-container fade-in">
            <h3 className="section-title">AI Channel Insights</h3>

            <div className="charts-grid">
                <SentimentTrendChart data={trendData} />
                <SentimentDistributionChart data={distributionData} />
            </div>

            <div className="insights-bento-grid">
                {Object.entries(insights).map(([category, items], index) => (
                    <div key={category} className="bento-insight-card" style={{
                        '--accent-color': index === 0 ? 'var(--color-primary)' :
                            index === 1 ? 'var(--color-accent)' :
                                index === 2 ? 'var(--color-success)' :
                                    index === 3 ? 'var(--color-warning)' : 'var(--color-info)'
                    }}>
                        <div className="category-header">
                            <span className="category-dot" style={{ backgroundColor: 'var(--accent-color)' }}></span>
                            <h4>{category}</h4>
                        </div>
                        <ul className="insights-list">
                            {items.map((item, i) => (
                                <li key={i} className="insight-item">
                                    {item}
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>
        </div>
    );
}
