import { useState, useCallback } from 'react';
import { DashboardLayout } from './components/DashboardLayout';
import { ChannelSearch } from './components/ChannelSearch';
import { VideoGrid } from './components/VideoGrid';
import { HealthGauge } from './components/HealthGauge';
import { ReportsView } from './components/ReportsView';
import { SettingsView } from './components/SettingsView';
import './App.css';

function App() {
  const [activeChannel, setActiveChannel] = useState(null);
  const [videos, setVideos] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  const fetchChannelData = async (query) => {
    setIsLoading(true);
    setError(null);
    setActiveChannel(null); // Clear previous
    setVideos([]);

    // Determine if query is ID or Handle
    let endpoint = `http://localhost:8000/api/channel/${query}/analyze`;

    try {
      const res = await fetch(endpoint, { method: 'POST' });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to fetch channel');
      }

      const data = await res.json();
      setActiveChannel(data);

      // Fetch videos
      const vidRes = await fetch(`http://localhost:8000/api/channel/${query}/videos`);
      if (vidRes.ok) {
        const vData = await vidRes.json();
        // Sort by Date Descending
        vData.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
        setVideos(vData);
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVideoClick = useCallback(async (videoId) => {
    // Optimistic Update: Set status to processing
    setVideos(prev => prev.map(v =>
      v.id === videoId
        ? { ...v, analysis_status: 'processing' }
        : v
    ));

    try {
      const res = await fetch(`http://localhost:8000/api/video/${videoId}/analyze`, {
        method: 'POST'
      });

      if (!res.ok) throw new Error("Analysis Failed");

      const data = await res.json();
      // Update the specific video with the fresh data (sentiment score, etc) AND insights
      setVideos(prev => prev.map(v =>
        v.id === videoId
          ? { ...data.video, insights: data.insights, distribution: data.sentiment_distribution }
          : v
      ));

      // Update Global Health Gauge
      if (data.health_score !== undefined) {
        setActiveChannel(prev => ({
          ...prev,
          health_score: data.health_score
        }));
      }

    } catch (e) {
      console.error(e);
      setVideos(prev => prev.map(v =>
        v.id === videoId ? { ...v, analysis_status: 'error' } : v
      ));
    }
  }, []);

  const handleSelectChannelFromReports = (channelId) => {
    setActiveTab('dashboard');
    fetchChannelData(channelId);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'reports':
        return <ReportsView onSelectChannel={handleSelectChannelFromReports} />;
      case 'settings':
        return <SettingsView />;
      default:
        return (
          <div className="dashboard-content">
            <div className="dashboard-header">
              <h2>Overview</h2>
              <span className="subtitle">Track and analyze channel sentiment</span>
            </div>

            <ChannelSearch onSearch={fetchChannelData} isLoading={isLoading} />

            {error && (
              <div className="error-banner">
                <span>⚠️ {error}</span>
              </div>
            )}

            {activeChannel && !isLoading && (
              <div className="bento-layout-simple">
                <div className="health-gauge-center">
                  <HealthGauge score={activeChannel.health_score} />
                </div>
              </div>
            )}

            {activeChannel && <h3 className="section-title">Latest Videos</h3>}
            <VideoGrid videos={videos} onVideoClick={handleVideoClick} />
          </div>
        );
    }
  };

  return (
    <DashboardLayout activeTab={activeTab} onTabChange={setActiveTab}>
      {renderContent()}
    </DashboardLayout>
  );
}

export default App;
