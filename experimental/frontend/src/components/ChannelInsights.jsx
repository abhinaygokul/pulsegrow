import React from 'react';
import './ChannelInsights.css';

export function ChannelInsights({ insights }) {
    if (!insights) return null;

    return (
        <div className="channel-insights-container fade-in">
            <h3 className="section-title">AI Channel Insights</h3>
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
