import type { CalendarOutput as CalendarData } from '../types/agents';

interface CalendarOutputProps {
  data: CalendarData;
}

export function CalendarOutput({ data }: CalendarOutputProps) {
  return (
    <div className="output-card">
      <div className="output-card-label">Content Calendar</div>
      <h4>Content Calendar</h4>

      <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem' }}>
        <div className="output-field">
          <div className="output-field-label">Duration</div>
          <div className="output-field-value">{data.campaign_duration}</div>
        </div>
        <div className="output-field">
          <div className="output-field-label">Frequency</div>
          <div className="output-field-value">{data.posting_frequency}</div>
        </div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Channel Strategies</div>
        {data.channel_strategies.map((cs, i) => (
          <div key={i} style={{ marginBottom: '0.5rem' }}>
            <span className="tag" style={{ marginRight: '0.5rem' }}>{cs.channel}</span>
            <span className="output-field-value" style={{ fontSize: '0.85rem' }}>{cs.strategy}</span>
          </div>
        ))}
      </div>

      <div className="output-field" style={{ marginTop: '1rem' }}>
        <div className="output-field-label">Content Mix Rationale</div>
        <div className="output-field-value">{data.content_mix_rationale}</div>
      </div>

      <div className="output-field" style={{ marginTop: '1rem' }}>
        <div className="output-field-label">Schedule</div>
        <div style={{ overflowX: 'auto' }}>
          <table className="calendar-table">
            <thead>
              <tr>
                <th>Week</th>
                <th>Day</th>
                <th>Channel</th>
                <th>Type</th>
                <th>Topic</th>
              </tr>
            </thead>
            <tbody>
              {data.entries.map((entry, i) => (
                <tr key={i}>
                  <td>{entry.week}</td>
                  <td>{entry.day}</td>
                  <td><span className="tag">{entry.channel}</span></td>
                  <td>{entry.content_type}</td>
                  <td>
                    <div>{entry.topic}</div>
                    <div style={{
                      fontSize: '0.8rem',
                      color: 'var(--text-secondary)',
                      marginTop: '0.2rem',
                      fontStyle: 'italic',
                    }}>
                      {entry.caption_hook}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
