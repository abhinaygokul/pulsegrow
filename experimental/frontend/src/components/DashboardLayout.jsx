import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import './DashboardLayout.css';

export function DashboardLayout({ children, activeTab, onTabChange }) {
    return (
        <div className="dashboard-layout">
            <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
            <main className="dashboard-main">
                <header className="top-bar">
                    <div className="breadcrumbs">
                        <span className="crumb-root">PulseGrow</span>
                        <span className="crumb-separator">/</span>
                        <span className="crumb-page">{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</span>
                    </div>
                </header>
                <div className="content-area">
                    {children}
                </div>
            </main>
        </div>
    );
}
