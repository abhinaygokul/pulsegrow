import React, { useState } from 'react';
import './SettingsView.css';

export function SettingsView() {
    const [isResetting, setIsResetting] = useState(false);
    const [message, setMessage] = useState(null);

    const handleReset = async () => {
        if (!window.confirm("Are you sure? This will delete all analyzed channels, videos, and comments.")) return;

        setIsResetting(true);
        setMessage(null);
        try {
            const res = await fetch('http://localhost:8000/api/admin/reset', { method: 'DELETE' });
            if (res.ok) {
                setMessage({ type: 'success', text: 'Database cleared successfully.' });
            } else {
                throw new Error("Failed to reset database");
            }
        } catch (err) {
            setMessage({ type: 'error', text: err.message });
        } finally {
            setIsResetting(false);
        }
    };

    return (
        <div className="settings-view fade-in">
            <div className="settings-section">
                <h3 className="section-title">System Management</h3>
                <div className="settings-card danger-zone">
                    <div className="settings-info">
                        <h4>Reset Database</h4>
                        <p>Wipe all stored data and start fresh. This action cannot be undone.</p>
                    </div>
                    <button
                        className="danger-btn"
                        onClick={handleReset}
                        disabled={isResetting}
                    >
                        {isResetting ? 'Resetting...' : 'Factory Reset'}
                    </button>
                </div>
            </div>

            <div className="settings-section">
                <h3 className="section-title">Analysis Preferences</h3>
                <div className="settings-card">
                    <div className="settings-info">
                        <h4>Sentiment Engine</h4>
                        <p>Choose the model used for comment analysis.</p>
                    </div>
                    <select className="settings-select" disabled>
                        <option>VADER (Fast, Local)</option>
                        <option>Gemini (Advanced, Cloud)</option>
                    </select>
                </div>
            </div>

            {message && (
                <div className={`settings-message ${message.type}`}>
                    {message.text}
                </div>
            )}

            <div className="settings-footer">
                <span>PulseGrow v1.2.0</span>
                <span>•</span>
                <span>System Status: Optimal</span>
            </div>
        </div>
    );
}
