import type { BriefParserOutput } from '../types/agents';

interface BriefOutputProps {
  data: BriefParserOutput;
}

export function BriefOutput({ data }: BriefOutputProps) {
  return (
    <div className="output-card">
      <div className="output-card-label">Brief Parser</div>
      <h4>{data.campaign_name}</h4>

      <div className="output-field">
        <div className="output-field-label">Client</div>
        <div className="output-field-value">{data.client_name}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Summary</div>
        <div className="output-field-value">{data.raw_summary}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Target Audience</div>
        <div className="output-field-value">{data.target_audience}</div>
      </div>

      {data.budget && (
        <div className="output-field">
          <div className="output-field-label">Budget</div>
          <div className="output-field-value">{data.budget}</div>
        </div>
      )}

      <div className="output-field">
        <div className="output-field-label">Timeline</div>
        <div className="output-field-value">{data.timeline}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Objectives</div>
        <ul className="bullet-list">
          {data.objectives.map((obj, i) => <li key={i}>{obj}</li>)}
        </ul>
      </div>

      <div className="output-field">
        <div className="output-field-label">KPIs</div>
        <div className="tag-list">
          {data.kpis.map((kpi, i) => <span key={i} className="tag">{kpi}</span>)}
        </div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Channels</div>
        <div className="tag-list">
          {data.channels.map((ch, i) => <span key={i} className="tag">{ch}</span>)}
        </div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Key Messages</div>
        <ul className="bullet-list">
          {data.key_messages.map((msg, i) => <li key={i}>{msg}</li>)}
        </ul>
      </div>

      <div className="output-field">
        <div className="output-field-label">Constraints</div>
        <ul className="bullet-list">
          {data.constraints.map((c, i) => <li key={i}>{c}</li>)}
        </ul>
      </div>

      {data.missing_fields.length > 0 && (
        <div className="output-field">
          <div className="output-field-label" style={{ color: 'var(--status-error)' }}>
            Missing Fields
          </div>
          <div className="tag-list">
            {data.missing_fields.map((f, i) => (
              <span key={i} className="tag" style={{ borderColor: 'var(--status-error)' }}>{f}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
