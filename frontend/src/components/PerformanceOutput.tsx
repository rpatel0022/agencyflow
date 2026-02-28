import type { PerformanceOutput as PerformanceData } from '../types/agents';

interface PerformanceOutputProps {
  data: PerformanceData;
}

function ratingClass(rating: string): string {
  const lower = rating.toLowerCase();
  if (lower.includes('exceptional')) return 'exceptional';
  if (lower.includes('strong')) return 'strong';
  if (lower.includes('moderate')) return 'moderate';
  return 'underperforming';
}

export function PerformanceOutput({ data }: PerformanceOutputProps) {
  return (
    <div className="output-card">
      <div className="output-card-label">Performance Report</div>
      <h4>Campaign Performance</h4>

      <div className="output-field">
        <div className="output-field-label">Overall</div>
        <div className="output-field-value" style={{ color: 'var(--accent-gold)' }}>
          {data.overall_performance}
        </div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Executive Summary</div>
        <div className="output-field-value">{data.executive_summary}</div>
      </div>

      <div className="output-field" style={{ marginTop: '1rem' }}>
        <div className="output-field-label">Key Metrics</div>
        <div className="metrics-grid">
          {data.key_metrics_summary.map((metric, i) => (
            <div key={i} className="metric-card">
              <div className="metric-name">{metric.metric_name}</div>
              <div className="metric-value">{metric.value}</div>
              <div className={`metric-trend ${metric.trend}`}>
                {metric.trend === 'up' ? '\u2191' : metric.trend === 'down' ? '\u2193' : '\u2192'} {metric.trend}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Channel Analysis</div>
        {data.channel_analysis.map((channel, i) => (
          <div key={i} className="channel-card">
            <div className="channel-header">
              <h5>{channel.channel}</h5>
              <span className={`rating-badge ${ratingClass(channel.performance_rating)}`}>
                {channel.performance_rating}
              </span>
            </div>
            <div className="output-field">
              <div className="output-field-label">Key Metric</div>
              <div className="output-field-value">{channel.key_metric}</div>
            </div>
            <div className="output-field">
              <div className="output-field-label">Insight</div>
              <div className="output-field-value">{channel.insight}</div>
            </div>
            <div className="output-field">
              <div className="output-field-label">Recommendation</div>
              <div className="output-field-value">{channel.recommendation}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="output-field">
        <div className="output-field-label">Top Performing Content</div>
        <ul className="bullet-list">
          {data.top_performing_content.map((c, i) => <li key={i}>{c}</li>)}
        </ul>
      </div>

      <div className="output-field">
        <div className="output-field-label">Recommendations</div>
        <ul className="bullet-list">
          {data.recommendations.map((r, i) => <li key={i}>{r}</li>)}
        </ul>
      </div>

      <div className="output-field">
        <div className="output-field-label">Next Steps</div>
        <ul className="bullet-list">
          {data.next_steps.map((s, i) => <li key={i}>{s}</li>)}
        </ul>
      </div>
    </div>
  );
}
