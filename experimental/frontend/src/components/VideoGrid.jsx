import React from 'react';
import { VideoCard } from './VideoCard';
import './VideoGrid.css';

export function VideoGrid({ videos, onVideoClick }) {
    if (!videos || videos.length === 0) {
        return <div className="no-videos">No videos found.</div>;
    }

    return (
        <div className="video-grid">
            {videos.map(video => (
                <VideoCard
                    key={video.id}
                    video={video}
                    onAnalyze={onVideoClick}
                />
            ))}
        </div>
    );
}
