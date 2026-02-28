import type { AgentName, AgentStep, PipelineOutputs } from '../types/pipeline';
import type {
  BriefParserOutput,
  AudienceOutput as AudienceData,
  CalendarOutput as CalendarData,
  CreativeBriefOutput as CreativeBriefData,
  PerformanceOutput as PerformanceData,
} from '../types/agents';
import { AGENT_DISPLAY_NAMES } from '../types/pipeline';
import { BriefOutput } from './BriefOutput';
import { AudienceOutput } from './AudienceOutput';
import { CalendarOutput } from './CalendarOutput';
import { CreativeBriefOutput } from './CreativeBriefOutput';
import { PerformanceOutput } from './PerformanceOutput';

interface DashboardProps {
  selectedAgent: AgentName | null;
  outputs: PipelineOutputs;
  error: string | null;
  steps: AgentStep[];
}

export function Dashboard({ selectedAgent, outputs, error, steps }: DashboardProps) {
  if (error) {
    return (
      <div className="error-banner">
        <div className="error-title">Pipeline Failed</div>
        <div>{error}</div>
        <div className="error-hint">Click "New Run" to try again.</div>
      </div>
    );
  }

  if (!selectedAgent) {
    const hasOutputs = Object.keys(outputs).length > 0;
    const isRunning = steps.some((s) => s.status === 'running');

    if (!hasOutputs && !isRunning) {
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
        {isRunning && <LoadingSkeleton steps={steps} />}
      </div>
    );
  }

  const step = steps.find((s) => s.name === selectedAgent);

  if (step?.status === 'failed') {
    return (
      <div className="error-banner">
        <div className="error-title">{AGENT_DISPLAY_NAMES[selectedAgent]} Failed</div>
        <div>This agent encountered an error during execution.</div>
      </div>
    );
  }

  switch (selectedAgent) {
    case 'brief_parser':
      return outputs.brief_parser
        ? <BriefOutput data={outputs.brief_parser as BriefParserOutput} />
        : <Pending name="Brief Parser" running={step?.status === 'running'} />;
    case 'audience_researcher':
      return outputs.audience_researcher
        ? <AudienceOutput data={outputs.audience_researcher as AudienceData} />
        : <Pending name="Audience Research" running={step?.status === 'running'} />;
    case 'content_calendar':
      return outputs.content_calendar
        ? <CalendarOutput data={outputs.content_calendar as CalendarData} />
        : <Pending name="Content Calendar" running={step?.status === 'running'} />;
    case 'creative_brief':
      return outputs.creative_brief
        ? <CreativeBriefOutput data={outputs.creative_brief as CreativeBriefData} />
        : <Pending name="Creative Brief" running={step?.status === 'running'} />;
    case 'performance_reporter':
      return outputs.performance_reporter
        ? <PerformanceOutput data={outputs.performance_reporter as PerformanceData} />
        : <Pending name="Performance Reporter" running={step?.status === 'running'} />;
  }
}

function Pending({ name, running }: { name: string; running?: boolean }) {
  if (running) {
    return (
      <div className="output-card skeleton-card">
        <div className="output-card-label">{name}</div>
        <div className="skeleton-line skeleton-title" />
        <div className="skeleton-line skeleton-text" />
        <div className="skeleton-line skeleton-text short" />
        <div className="skeleton-line skeleton-text" />
      </div>
    );
  }

  return (
    <div className="welcome">
      <p style={{ color: 'var(--text-secondary)' }}>{name} — waiting in queue.</p>
    </div>
  );
}

function LoadingSkeleton({ steps }: { steps: AgentStep[] }) {
  const running = steps.find((s) => s.status === 'running');
  if (!running) return null;

  return (
    <div className="output-card skeleton-card">
      <div className="output-card-label">{AGENT_DISPLAY_NAMES[running.name]}</div>
      <div className="skeleton-line skeleton-title" />
      <div className="skeleton-line skeleton-text" />
      <div className="skeleton-line skeleton-text short" />
    </div>
  );
}
