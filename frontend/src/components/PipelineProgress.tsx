import type { AgentName, AgentStep } from '../types/pipeline';
import { AGENT_DISPLAY_NAMES } from '../types/pipeline';

interface PipelineProgressProps {
  steps: AgentStep[];
  selectedAgent: AgentName | null;
  onSelectAgent: (name: AgentName) => void;
}

function formatElapsed(ms?: number): string {
  if (ms === undefined) return '';
  const seconds = Math.round(ms / 1000);
  return `${seconds}s`;
}

export function PipelineProgress({ steps, selectedAgent, onSelectAgent }: PipelineProgressProps) {
  return (
    <div>
      <div className="sidebar-title">Pipeline</div>
      {steps.map((step) => (
        <div
          key={step.name}
          className={`pipeline-step ${selectedAgent === step.name ? 'active' : ''}`}
          onClick={() => step.status !== 'pending' && onSelectAgent(step.name)}
          style={{ cursor: step.status === 'pending' ? 'default' : 'pointer', opacity: step.status === 'pending' ? 0.5 : 1 }}
        >
          <div className={`step-indicator ${step.status}`} />
          <span className="step-name">{AGENT_DISPLAY_NAMES[step.name]}</span>
          {step.elapsedMs !== undefined && (
            <span className="step-time">{formatElapsed(step.elapsedMs)}</span>
          )}
        </div>
      ))}
    </div>
  );
}
