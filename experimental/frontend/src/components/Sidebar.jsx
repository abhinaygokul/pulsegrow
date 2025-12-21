import React from 'react';
import './Sidebar.css';

export function Sidebar({ activeTab, onTabChange }) {
    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: '📊' },
        { id: 'reports', label: 'Reports', icon: '📑' },
        { id: 'settings', label: 'Settings', icon: '⚙️' },
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="logo-icon">P</div>
                <span className="logo-text">PulseGrow</span>
            </div>

            <nav className="sidebar-nav">
                {menuItems.map((item) => (
                    <button
                        key={item.id}
                        className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                        onClick={() => onTabChange(item.id)}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span className="nav-label">{item.label}</span>
                    </button>
                ))}
            </nav>

            <div className="sidebar-footer">
                <div className="user-profile">
                    <div className="avatar">U</div>
                    <div className="user-info">
                        <div className="user-name">User</div>
                        <div className="user-role">Creator</div>
                    </div>
                </div>
            </div>
        </aside>
    );
}
