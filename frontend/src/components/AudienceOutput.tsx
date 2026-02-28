import type { AudienceOutput as AudienceData } from '../types/agents';

interface AudienceOutputProps {
  data: AudienceData;
}

export function AudienceOutput({ data }: AudienceOutputProps) {
  return (
    <div className="output-card">
      <div className="output-card-label">Audience Research</div>
      <h4>Target Audience Analysis</h4>

      <div className="output-field">
        <div className="output-field-label">Audience Size</div>
        <div className="output-field-value">{data.audience_size_estimate}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Suggested Tone</div>
        <div className="output-field-value">{data.suggested_tone}</div>
      </div>

      <div className="output-field">
        <div className="output-field-label">Personas</div>
        {data.personas.map((persona, i) => (
          <div key={i} className="persona-card">
            <h5>{persona.name}</h5>
            <div className="persona-age">{persona.age_range}</div>
            <p className="output-field-value" style={{ marginBottom: '0.75rem' }}>
              {persona.description}
            </p>

            <div className="output-field">
              <div className="output-field-label">Motivations</div>
              <ul className="bullet-list">
                {persona.motivations.map((m, j) => <li key={j}>{m}</li>)}
              </ul>
            </div>

            <div className="output-field">
              <div className="output-field-label">Pain Points</div>
              <ul className="bullet-list">
                {persona.pain_points.map((p, j) => <li key={j}>{p}</li>)}
              </ul>
            </div>

            <div className="output-field">
              <div className="output-field-label">Channels</div>
              <div className="tag-list">
                {persona.preferred_channels.map((ch, j) => (
                  <span key={j} className="tag">{ch}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="output-field">
        <div className="output-field-label">Key Insights</div>
        <ul className="bullet-list">
          {data.key_insights.map((insight, i) => <li key={i}>{insight}</li>)}
        </ul>
      </div>

      <div className="output-field">
        <div className="output-field-label">Targeting Recommendations</div>
        <ul className="bullet-list">
          {data.targeting_recommendations.map((rec, i) => <li key={i}>{rec}</li>)}
        </ul>
      </div>
    </div>
  );
}
