import React, { useState, useEffect } from 'react';
import './ReportsView.css';

export function ReportsView({ onSelectChannel }) {
    const [stats, setStats] = useState(null);
    const [channels, setChannels] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchReportsData = async () => {
            try {
                const [statsRes, channelsRes] = await Promise.all([
                    fetch('http://localhost:8000/api/admin/stats'),
                    fetch('http://localhost:8000/api/channels')
                ]);

                if (statsRes.ok) setStats(await statsRes.json());
                if (channelsRes.ok) setChannels(await channelsRes.json());
            } catch (err) {
                console.error("Failed to fetch reports:", err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchReportsData();
    }, []);

    if (isLoading) return <div className="loading-state">Loading Reports...</div>;

    return (
        <div className="reports-view fade-in">
            <div className="reports-grid">
                {/* Global Stats Cards */}
                <div className="stat-card">
                    <span className="stat-label">Total Channels</span>
                    <span className="stat-value">{stats?.total_channels || 0}</span>
                </div>
                <div className="stat-card">
                    <span className="stat-label">Videos Tracked</span>
                    <span className="stat-value">{stats?.total_videos || 0}</span>
                </div>
                <div className="stat-card">
                    <span className="stat-label">Global Sentiment</span>
                    <span className="stat-value" style={{
                        color: stats?.global_sentiment_average > 0 ? 'var(--color-success)' : 'var(--color-error)'
                    }}>
                        {(stats?.global_sentiment_average || 0).toFixed(2)}
                    </span>
                </div>
            </div>

            <h3 className="section-title">Analysis History</h3>
            <div className="history-list">
                {channels.length === 0 ? (
                    <div className="empty-history">No channels analyzed yet.</div>
                ) : (
                    <div className="history-table-container">
                        <table className="history-table">
                            <thead>
                                <tr>
                                    <th>Channel</th>
                                    <th>Health Score</th>
                                    <th>Last Updated</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {channels.map(channel => (
                                    <tr key={channel.id}>
                                        <td className="channel-cell">
                                            <img src={channel.thumbnail_url} alt="" className="mini-thumb" />
                                            <span>{channel.title}</span>
                                        </td>
                                        <td>
                                            <span className="health-pill" style={{
                                                backgroundColor: channel.health_score > 0 ? 'var(--color-success-container)' : 'var(--color-error-container)',
                                                color: channel.health_score > 0 ? 'var(--color-success)' : 'var(--color-error)'
                                            }}>
                                                {(channel.health_score || 0).toFixed(2)}
                                            </span>
                                        </td>
                                        <td>{new Date(channel.last_updated).toLocaleDateString()}</td>
                                        <td>
                                            <button
                                                className="view-btn-sm"
                                                onClick={() => onSelectChannel(channel.id)}
                                            >
                                                View Dashboard
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
