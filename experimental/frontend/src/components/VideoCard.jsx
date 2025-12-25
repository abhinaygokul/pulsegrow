import React from 'react';
import { GeminiInsights } from './GeminiInsights';
import './VideoCard.css';

export function VideoCard({ video, onAnalyze }) {
    const isAnalyzed = video.analysis_status === 'completed';
    const isProcessing = video.analysis_status === 'processing';

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
                            {isProcessing
                                ? (video.total > 0
                                    ? `Analyzing (${video.progress} / ${video.total})...`
                                    : 'Initializing...')
                                : 'Analyze Sentiment'}
                        </button>

                    ) : (
                        <div className="analysis-simple-container">
                            {video.top_50_analysis && (
                                <GeminiInsights data={video.top_50_analysis} />
                            )}

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
