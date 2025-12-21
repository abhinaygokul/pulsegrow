import React, { useState } from 'react';
import './ChannelSearch.css';

export function ChannelSearch({ onSearch, isLoading }) {
    const [channelId, setChannelId] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (channelId.trim()) {
            onSearch(channelId.trim());
        }
    };

    return (
        <div className="channel-search-container">
            <form onSubmit={handleSubmit} className="search-form">
                <div className="input-group">
                    <input
                        type="text"
                        className="search-input"
                        placeholder="Enter Channel ID or Handle (e.g., @mkbhd)"
                        value={channelId}
                        onChange={(e) => setChannelId(e.target.value)}
                        disabled={isLoading}
                    />
                    <button type="submit" className="search-btn" disabled={isLoading}>
                        {isLoading ? 'Analyzing...' : 'Analyze Channel'}
                    </button>
                </div>
                <p className="search-hint">Try "demo" for a quick preview.</p>
            </form>
        </div>
    );
}
