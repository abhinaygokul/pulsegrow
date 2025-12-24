import React from 'react';
import './GeminiInsights.css';

export function GeminiInsights({ data }) {
    if (!data) return null;

    if (data.error) {
        return (
            <div className="gemini-insights-container error-state">
                <div className="gemini-header">
                    <span className="ai-badge error">⚠️ Analysis Warning</span>
                </div>
                <div className="error-message">
                    {data.error}
                    <br />
                    <small>(Check backend logs or .env file)</small>
                </div>
            </div>
        );
    }

    const {
        sentiment_summary,
        sentiment_breakdown,
        key_themes,
        praise_summary,
        criticism_summary,
        ai_insights,
        notable_quotes
    } = data;

    return (
        <div className="gemini-insights-container">
            <div className="gemini-header">
                <span className="ai-badge">✨ Gemini 2.0 AI Analysis</span>
                <h3>Top 50 Comment Insights</h3>
            </div>

            {/* 1. Summary & Sentiment */}
            <div className="gemini-section summary-section">
                <div className="summary-text">
                    <strong>Executive Summary:</strong> {sentiment_summary}
                </div>
                {sentiment_breakdown && (
                    <div className="sentiment-bar-container">
                        <div className="sentiment-bar-segments">
                            <div className="segment pos" style={{ flex: sentiment_breakdown.positive || 1 }}></div>
                            <div className="segment neu" style={{ flex: sentiment_breakdown.neutral || 1 }}></div>
                            <div className="segment neg" style={{ flex: sentiment_breakdown.negative || 1 }}></div>
                        </div>
                        <div className="sentiment-labels">
                            <span className="pos-label">{sentiment_breakdown.positive}% Positive</span>
                            <span className="neu-label">{sentiment_breakdown.neutral}% Neutral</span>
                            <span className="neg-label">{sentiment_breakdown.negative}% Negative</span>
                        </div>
                    </div>
                )}
            </div>

            <div className="gemini-grid">
                {/* 2. Key Themes */}
                <div className="gemini-card themes-card">
                    <h4>🔥 Key Themes</h4>
                    <div className="tags-cloud">
                        {key_themes && key_themes.map((theme, i) => (
                            <span key={i} className="theme-tag">{theme}</span>
                        ))}
                    </div>
                </div>

                {/* 3. Likes & Dislikes */}
                <div className="gemini-card feedback-card">
                    <div className="feedback-col">
                        <h4>👍 What They Like</h4>
                        <p>{praise_summary}</p>
                    </div>
                    <div className="feedback-divider"></div>
                    <div className="feedback-col">
                        <h4>👎 What They Want Improved</h4>
                        <p>{criticism_summary}</p>
                    </div>
                </div>
            </div>

            {/* 4. Actionable Insights */}
            <div className="gemini-section insights-section">
                <h4>🚀 Creator Action Plan</h4>
                <ul className="insights-list">
                    {ai_insights && ai_insights.map((insight, i) => (
                        <li key={i}>{insight}</li>
                    ))}
                </ul>
            </div>

            {/* 5. Notable Quotes */}
            {notable_quotes && notable_quotes.length > 0 && (
                <div className="gemini-section quotes-section">
                    <h4>💬 Notable Quotes</h4>
                    <div className="quotes-grid">
                        {notable_quotes.map((q, i) => (
                            <div key={i} className="quote-item">
                                <p>"{q.text}"</p>
                                <div className="quote-meta">
                                    <span className="author">{q.author}</span>
                                    <span className="likes">❤️ {q.likes}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
