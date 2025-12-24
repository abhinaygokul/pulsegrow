import { useState, useCallback } from 'react';
import { DashboardLayout } from './components/DashboardLayout';
import { ChannelSearch } from './components/ChannelSearch';
import { VideoGrid } from './components/VideoGrid';
import { HealthGauge } from './components/HealthGauge';
import { ChannelInsights } from './components/ChannelInsights';
import { ReportsView } from './components/ReportsView';
import { SettingsView } from './components/SettingsView';
import './App.css';

function App() {
  const [activeChannel, setActiveChannel] = useState(null);
  const [videos, setVideos] = useState([]);
  const [channelInsights, setChannelInsights] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  const fetchChannelData = async (query) => {
    setIsLoading(true);
    setError(null);
    setActiveChannel(null); // Clear previous
    setVideos([]);
    setChannelInsights(null);

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

      // Fetch Global Channel Insights
      const insightsRes = await fetch(`http://localhost:8000/api/channel/${query}/insights`);
      if (insightsRes.ok) {
        const iData = await insightsRes.json();
        setChannelInsights(iData);
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
        ? { ...v, analysis_status: 'processing', progress: 0, total: 0 }
        : v
    ));

    try {
      const response = await fetch(`http://localhost:8000/api/video/${videoId}/analyze`, {
        method: 'POST'
      });

      if (!response.ok) throw new Error("Analysis Failed");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.status === 'processing') {
                setVideos(prev => prev.map(v =>
                  v.id === videoId
                    ? { ...v, progress: data.progress, total: data.total }
                    : v
                ));
              } else if (data.status === 'completed') {
                setVideos(prev => prev.map(v =>
                  v.id === videoId
                    ? {
                      ...v,
                      ...data.video,
                      analysis_status: 'completed',
                      insights: data.insights,
                      distribution: data.distribution,
                      top_50_analysis: data.top_50_analysis
                    }
                    : v
                ));

                // Update Health Gauge
                if (data.health_score !== undefined) {
                  setActiveChannel(prev => ({ ...prev, health_score: data.health_score }));
                }

                // Refresh Channel Insights
                if (activeChannel?.id || activeChannel?.channel_id) {
                  const cId = activeChannel.id || activeChannel.channel_id;
                  const cInsightsRes = await fetch(`http://localhost:8000/api/channel/${cId}/insights`);
                  if (cInsightsRes.ok) {
                    const cIData = await cInsightsRes.json();
                    setChannelInsights(cIData);
                  }
                }
              }
            } catch (jsonErr) {
              console.warn("Failed to parse SSE chunk", jsonErr);
            }
          }
        }
      }
    } catch (e) {
      console.error("Analysis Error:", e);
      setVideos(prev => prev.map(v =>
        v.id === videoId ? { ...v, analysis_status: 'error' } : v
      ));
    }
  }, [activeChannel]);


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

            {channelInsights && <ChannelInsights insights={channelInsights} videos={videos} />}

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
