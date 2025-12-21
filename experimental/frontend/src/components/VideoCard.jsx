import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import './VideoCard.css';

export function VideoCard({ video, onAnalyze }) {
    const isAnalyzed = video.analysis_status === 'completed';
    const isProcessing = video.analysis_status === 'processing';

    // Prepare Pie Data if analyzed
    const pieData = [
        { name: 'Positive', value: (video.distribution?.positive || 0) * 100, color: '#4ade80' },
        { name: 'Neutral', value: (video.distribution?.neutral || 0) * 100, color: '#94a3b8' },
        { name: 'Negative', value: (video.distribution?.negative || 0) * 100, color: '#f87171' },
    ];

    // Fallback if no data or not analyzed
    if (!isAnalyzed || pieData.every(d => d.value === 0)) {
        pieData[1].value = 100; // Show neutral circle
    }

    return (
        <div className={`video-card horizontal ${isAnalyzed ? 'analyzed' : ''}`}>
            <div className="card-media-small">
                <img
                    src={video.thumbnail_url || 'https://via.placeholder.com/320x180'}
                    alt={video.title}
                    className="card-thumb"
                />
            </div>

            <div className="card-content">
                <div className="content-top">
                    <div className="title-group">
                        <h3 className="card-title" title={video.title}>{video.title}</h3>
                        <p className="card-date">{new Date(video.published_at).toLocaleDateString()}</p>
                    </div>
                    <span className="views-badge-minimal">{new Intl.NumberFormat('en-US', { notation: "compact" }).format(video.view_count)} views</span>
                </div>

                <div className="card-actions-dynamic">
                    {!isAnalyzed ? (
                        <button
                            className="action-btn analyze-btn-lg"
                            onClick={() => onAnalyze(video.id)}
                            disabled={isProcessing}
                        >
                            {isProcessing ? 'Analyzing...' : 'Analyze Sentiment'}
                        </button>
                    ) : (
                        <div className="analysis-layout">
                            {/* Larger Pie Chart Section */}
                            <div className="large-chart-section">
                                <div className="large-chart-container">
                                    <ResponsiveContainer width="100%" height={140}>
                                        <PieChart>
                                            <Tooltip
                                                formatter={(value) => `${value.toFixed(0)}%`}
                                                contentStyle={{
                                                    borderRadius: '8px',
                                                    border: 'none',
                                                    boxShadow: 'var(--shadow-md)',
                                                    fontSize: '0.8rem',
                                                    fontWeight: 'bold'
                                                }}
                                            />
                                            <Pie
                                                data={pieData}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={35}
                                                outerRadius={55}
                                                paddingAngle={4}
                                                dataKey="value"
                                                nameKey="name"
                                                stroke="none"
                                                isAnimationActive={false}
                                            >
                                                {pieData.map((entry, index) => (
                                                    <Cell
                                                        key={`cell-${index}`}
                                                        fill={entry.color}
                                                        style={{ cursor: 'pointer', outline: 'none' }}
                                                    />
                                                ))}
                                            </Pie>
                                        </PieChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="score-summary">
                                    <div className="sentiment-score-huge" style={{
                                        color: video.sentiment_score > 0 ? 'var(--color-success)' : video.sentiment_score < 0 ? 'var(--color-error)' : 'var(--color-text-muted)'
                                    }}>
                                        {video.sentiment_score > 0 ? '+' : ''}{video.sentiment_score.toFixed(2)}
                                    </div>
                                    <span className="sentiment-label-compact">Score</span>

                                    <div className="sentiment-legend-mini">
                                        <div className="legend-item"><span className="dot pos"></span> Pos</div>
                                        <div className="legend-item"><span className="dot neu"></span> Neu</div>
                                        <div className="legend-item"><span className="dot neg"></span> Neg</div>
                                    </div>
                                </div>
                            </div>

                            {/* Categorized Insights */}
                            <div className="categorized-insights-grid">
                                {video.insights && typeof video.insights === 'object' && !Array.isArray(video.insights) ? (
                                    Object.entries(video.insights).map(([category, items]) => (
                                        <div key={category} className="insight-cat-item">
                                            <h4 className="cat-title">{category}</h4>
                                            <ul className="cat-list">
                                                {items.map((item, i) => (
                                                    <li key={i}>{item}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    ))
                                ) : (
                                    <div className="insight-cat-item">
                                        <h4 className="cat-title">Insights</h4>
                                        <ul className="cat-list">
                                            {(video.insights || []).slice(0, 3).map((insight, i) => (
                                                <li key={i}>{insight}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>

                            <button
                                className="reanalyze-btn-minimal"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onAnalyze(video.id);
                                }}
                                disabled={isProcessing}
                            >
                                {isProcessing ? 'Refreshing...' : '↻ Refresh'}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
