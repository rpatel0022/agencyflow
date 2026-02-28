import type { AgentName, PipelineOutputs } from '../types/pipeline';
import type {
  BriefParserOutput,
  AudienceOutput as AudienceData,
  CalendarOutput as CalendarData,
  CreativeBriefOutput as CreativeBriefData,
  PerformanceOutput as PerformanceData,
} from '../types/agents';
import { BriefOutput } from './BriefOutput';
import { AudienceOutput } from './AudienceOutput';
import { CalendarOutput } from './CalendarOutput';
import { CreativeBriefOutput } from './CreativeBriefOutput';
import { PerformanceOutput } from './PerformanceOutput';

interface DashboardProps {
  selectedAgent: AgentName | null;
  outputs: PipelineOutputs;
  error: string | null;
}

export function Dashboard({ selectedAgent, outputs, error }: DashboardProps) {
  if (error) {
    return <div className="error-banner">{error}</div>;
  }

  if (!selectedAgent) {
    // Show all completed outputs stacked
    const hasOutputs = Object.keys(outputs).length > 0;
    if (!hasOutputs) {
      return (
        <div className="welcome">
          <p style={{ color: 'var(--text-secondary)' }}>
            Pipeline running — outputs will appear as agents complete.
          </p>
        </div>
      );
    }

    return (
      <div>
        {outputs.brief_parser && <BriefOutput data={outputs.brief_parser as BriefParserOutput} />}
        {outputs.audience_researcher && <AudienceOutput data={outputs.audience_researcher as AudienceData} />}
        {outputs.content_calendar && <CalendarOutput data={outputs.content_calendar as CalendarData} />}
        {outputs.creative_brief && <CreativeBriefOutput data={outputs.creative_brief as CreativeBriefData} />}
        {outputs.performance_reporter && <PerformanceOutput data={outputs.performance_reporter as PerformanceData} />}
      </div>
    );
  }

  // Show selected agent's output
  switch (selectedAgent) {
    case 'brief_parser':
      return outputs.brief_parser
        ? <BriefOutput data={outputs.brief_parser as BriefParserOutput} />
        : <Pending name="Brief Parser" />;
    case 'audience_researcher':
      return outputs.audience_researcher
        ? <AudienceOutput data={outputs.audience_researcher as AudienceData} />
        : <Pending name="Audience Research" />;
    case 'content_calendar':
      return outputs.content_calendar
        ? <CalendarOutput data={outputs.content_calendar as CalendarData} />
        : <Pending name="Content Calendar" />;
    case 'creative_brief':
      return outputs.creative_brief
        ? <CreativeBriefOutput data={outputs.creative_brief as CreativeBriefData} />
        : <Pending name="Creative Brief" />;
    case 'performance_reporter':
      return outputs.performance_reporter
        ? <PerformanceOutput data={outputs.performance_reporter as PerformanceData} />
        : <Pending name="Performance Reporter" />;
  }
}

function Pending({ name }: { name: string }) {
  return (
    <div className="welcome">
      <p style={{ color: 'var(--text-secondary)' }}>{name} — waiting for completion.</p>
    </div>
  );
}
