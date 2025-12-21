import React from 'react';
import './SentimentBadge.css';

export function SentimentBadge({ score, status }) {
    if (status === 'processing' || status === 'pending') {
        return <span className="badge badge-pending">Analyzing...</span>;
    }

    if (status === 'error') {
        return <span className="badge badge-error">Error</span>;
    }

    if (score === undefined || score === null) {
        return <span className="badge badge-neutral">-</span>;
    }

    // Score is typically -1.0 to 1.0 (or just simplified)
    let type = 'neutral';
    if (score > 0.05) type = 'positive';
    if (score < -0.05) type = 'negative';

    const percent = Math.round(score * 100);

    return (
        <span className={`badge badge-${type}`}>
            {type === 'positive' && '↑'}
            {type === 'negative' && '↓'}
            {type === 'neutral' && '•'}
            {' '}
            {percent}%
        </span>
    );
}
