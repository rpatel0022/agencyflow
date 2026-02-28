import type { CreativeBriefOutput as CreativeBriefData } from '../types/agents';

interface CreativeBriefOutputProps {
  data: CreativeBriefData;
}

export function CreativeBriefOutput({ data }: CreativeBriefOutputProps) {
  return (
    <div className="output-card">
      <div className="output-card-label">Creative Brief</div>
      <h4>{data.project_name}</h4>

      <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem' }}>
        <div className="output-field">
          <div className="output-field-label">Prepared For</div>
          <div className="output-field-value">{data.prepared_for}</div>
        </div>
        <div className="output-field">
          <div className="output-field-label">Date</div>
          <div className="output-field-value">{data.date}</div>
        </div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Background</div>
        <div className="output-field-value">{data.background}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Objective</div>
        <div className="output-field-value">{data.objective}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Target Audience</div>
        <div className="output-field-value">{data.target_audience_summary}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Key Message</div>
        <div className="output-field-value" style={{ fontSize: '1.1rem', fontStyle: 'italic', color: 'var(--accent-gold)' }}>
          {data.key_message}
        </div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Supporting Messages</div>
        <ul className="bullet-list">
          {data.supporting_messages.map((msg, i) => <li key={i}>{msg}</li>)}
        </ul>
      </div>

      <div className="output-field">
        <div className="output-field-label">Tone &amp; Voice</div>
        <div className="output-field-value">{data.tone_and_voice}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Visual Direction</div>
        <div className="output-field-value">{data.visual_direction}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Deliverables</div>
        <ul className="bullet-list">
          {data.deliverables.map((d, i) => <li key={i}>{d}</li>)}
        </ul>
      </div>

      <div className="output-field">
        <div className="output-field-label">Timeline</div>
        <div className="output-field-value">{data.timeline_summary}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Success Metrics</div>
        <div className="tag-list">
          {data.success_metrics.map((m, i) => <span key={i} className="tag">{m}</span>)}
        </div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Mandatory Inclusions</div>
        <ul className="bullet-list">
          {data.mandatory_inclusions.map((inc, i) => <li key={i}>{inc}</li>)}
        </ul>
      </div>
    </div>
  );
}
