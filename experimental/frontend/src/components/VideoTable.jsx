import React from 'react';
import { SentimentBadge } from './SentimentBadge';
import './VideoTable.css';

export function VideoTable({ videos, onVideoClick }) {
    if (!videos || videos.length === 0) {
        return <div className="no-data">No videos found. Start an analysis above.</div>;
    }

    return (
        <div className="table-container">
            <table className="video-table">
                <thead>
                    <tr>
                        <th className="th-video">Video</th>
                        <th>Published</th>
                        <th>Views</th>
                        <th>Likes</th>
                        <th>Sentiment</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {videos.map((video) => (
                        <tr key={video.id}>
                            <td className="td-video clickable" onClick={() => onVideoClick(video.id)}>
                                <img src={video.thumbnail_url} alt="" className="video-thumb" />
                                <div className="video-info">
                                    <div className="video-title" title={video.title}>{video.title}</div>
                                    <div className="video-id">{video.id}</div>
                                </div>
                            </td>
                            <td>{new Date(video.published_at).toLocaleDateString()}</td>
                            <td>{video.view_count?.toLocaleString()}</td>
                            <td>{video.like_count?.toLocaleString()}</td>
                            <td>
                                <SentimentBadge
                                    score={video.sentiment_score}
                                    status={video.analysis_status}
                                />
                            </td>
                            <td>
                                <button
                                    className="analyze-btn"
                                    onClick={() => onVideoClick(video.id)}
                                    disabled={video.analysis_status === 'processing' || video.analysis_status === 'completed'}
                                >
                                    {video.analysis_status === 'completed' ? 'Done' : 'Analyze'}
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
