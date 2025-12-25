import React, { useMemo } from 'react';
import './ChannelInsights.css';
import { SentimentTrendChart } from './SentimentTrendChart';
import { SentimentDistributionChart } from './SentimentDistributionChart';

export function ChannelInsights({ insights, videos }) {
    if (!insights) return null;

    // Calculate Trend Data from Videos for the Chart
    const trendData = useMemo(() => {
        if (!videos || videos.length === 0) return [];
        // Sort by date ascending for the chart
        const sorted = [...videos].sort((a, b) => new Date(a.published_at) - new Date(b.published_at));

        return sorted.map(v => {
            let pos = 0, neu = 0, neg = 0;

            if (v.distribution) {
                // Backend provides fractional 0.0-1.0
                pos = v.distribution.positive || 0;
                neu = v.distribution.neutral || 0;
                neg = v.distribution.negative || 0;
            } else if (v.sentiment_score !== undefined && v.sentiment_score !== null) {
                // Fallback 100% based on score threshold
                const s = v.sentiment_score;
                if (s >= 0.05) pos = 1.0;
                else if (s <= -0.05) neg = 1.0;
                else neu = 1.0;
            }

            return {
                title: v.title,
                date: new Date(v.published_at).toLocaleDateString(),
                positive: (pos * 100).toFixed(1), // Convert to percentage for readable chart
                neutral: (neu * 100).toFixed(1),
                negative: (neg * 100).toFixed(1)
            };
        });
    }, [videos]);

    // Calculate Distribution Data - Mathematical Aggregation
    const distributionData = useMemo(() => {
        if (!videos || videos.length === 0) return { positive: 0, neutral: 0, negative: 0 };

        let totalPos = 0, totalNeu = 0, totalNeg = 0;
        let count = 0;

        videos.forEach(v => {
            // Use precise distribution if available (from backend analysis)
            if (v.distribution) {
                totalPos += (v.distribution.positive || 0);
                totalNeu += (v.distribution.neutral || 0);
                totalNeg += (v.distribution.negative || 0);
                count++;
            }
            // Fallback: Estimate from score if detailed distribution is missing but analyzed
            else if (v.sentiment_score !== undefined && v.sentiment_score !== null) {
                const s = v.sentiment_score;
                if (s >= 0.05) totalPos += 1;
                else if (s <= -0.05) totalNeg += 1;
                else totalNeu += 1;
                count++;
            }
        });

        if (count === 0) return { positive: 0, neutral: 0, negative: 0 };

        // Average them out
        return {
            positive: totalPos / count,
            neutral: totalNeu / count,
            negative: totalNeg / count
        };
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
