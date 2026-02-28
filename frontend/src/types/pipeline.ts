// Pipeline state types

import type {
  BriefParserOutput,
  AudienceOutput,
  CalendarOutput,
  CreativeBriefOutput,
  PerformanceOutput,
} from './agents';

export type PipelineStatus =
  | 'idle'
  | 'parsing'
  | 'researching'
  | 'calendaring'
  | 'briefing'
  | 'reporting'
  | 'complete'
  | 'failed';

export type AgentName =
  | 'brief_parser'
  | 'audience_researcher'
  | 'content_calendar'
  | 'creative_brief'
  | 'performance_reporter';

export const AGENT_DISPLAY_NAMES: Record<AgentName, string> = {
  brief_parser: 'Brief Parser',
  audience_researcher: 'Audience Research',
  content_calendar: 'Content Calendar',
  creative_brief: 'Creative Brief',
  performance_reporter: 'Performance Reporter',
};

export const AGENT_ORDER: AgentName[] = [
  'brief_parser',
  'audience_researcher',
  'content_calendar',
  'creative_brief',
  'performance_reporter',
];

export interface AgentStep {
  name: AgentName;
  status: 'pending' | 'running' | 'complete' | 'failed';
  elapsedMs?: number;
}

export interface PipelineOutputs {
  brief_parser?: BriefParserOutput;
  audience_researcher?: AudienceOutput;
  content_calendar?: CalendarOutput;
  creative_brief?: CreativeBriefOutput;
  performance_reporter?: PerformanceOutput;
}

export interface SSEEvent {
  id: number;
  run_id: string;
  timestamp: string;
  event_type: string;
  agent_name?: string;
  status?: string;
  output?: Record<string, unknown>;
  elapsed_ms?: number;
  failed_agent?: string;
  error?: {
    agent_name: string;
    error_type: string;
    message: string;
    retryable: boolean;
  };
}

export interface DemoResponse {
  status: string;
  demo: boolean;
  outputs: {
    brief_parsed: BriefParserOutput;
    audience: AudienceOutput;
    calendar: CalendarOutput;
    creative_brief: CreativeBriefOutput;
    performance: PerformanceOutput;
  };
}
