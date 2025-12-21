import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import './HealthGauge.css';

export function HealthGauge({ score }) {
    // Keep raw score scale (-1 to 1) for consistency with VideoCards
    const displayScore = score || 0;
    const percentage = ((displayScore + 1) / 2) * 100;

    // Data for the gauge
    const data = [
        { value: Math.max(0.1, percentage) },
        { value: Math.max(0.1, 100 - percentage) }
    ];

    // Colors based on score
    const getStatusColor = () => {
        if (score > 0.4) return '#4ade80'; // Success
        if (score > -0.1) return '#facc15'; // Warning/Neutral
        return '#f87171'; // Error
    };

    const getStatusLabel = () => {
        if (score > 0.6) return 'EXCELLENT';
        if (score > 0.2) return 'HEALTHY';
        if (score > -0.2) return 'STABLE';
        if (score > -0.6) return 'UNSETTLED';
        return 'CRITICAL';
    };

    const statusColor = getStatusColor();

    return (
        <div className="health-gauge-premium">
            <div className="gauge-outer-ring" style={{ borderColor: `${statusColor}33` }}>
                <div className="gauge-container-inner">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={data}
                                cx="50%"
                                cy="50%"
                                startAngle={225}
                                endAngle={-45}
                                innerRadius="75%"
                                outerRadius="100%"
                                dataKey="value"
                                stroke="none"
                                strokeWidth={0}
                                animationBegin={0}
                                animationDuration={1000}
                            >
                                <Cell fill={statusColor} />
                                <Cell fill="var(--md-sys-color-surface-container-high)" />
                            </Pie>
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="gauge-center-content">
                        <span className="gauge-status-tag" style={{ backgroundColor: `${statusColor}22`, color: statusColor }}>
                            {getStatusLabel()}
                        </span>
                        <div className="gauge-score-large" style={{ color: 'var(--md-sys-color-on-surface)' }}>
                            {displayScore > 0 ? '+' : ''}{displayScore.toFixed(2)}
                        </div>
                        <span className="gauge-label-bottom">CHANNEL HEALTH</span>
                    </div>
                </div>
            </div>
            <div className="gauge-thresholds">
                <span className="threshold">POOR</span>
                <span className="threshold">NEUTRAL</span>
                <span className="threshold">GREAT</span>
            </div>
        </div>
    );
}
