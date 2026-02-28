// SSE connection manager — wraps EventSource for pipeline events

import { useCallback, useRef, useState } from 'react';
import type { AgentName, AgentStep, PipelineOutputs, PipelineStatus } from '../types/pipeline';
import type {
  BriefParserOutput,
  AudienceOutput,
  CalendarOutput,
  CreativeBriefOutput,
  PerformanceOutput,
} from '../types/agents';
import { AGENT_ORDER } from '../types/pipeline';

interface PipelineState {
  status: PipelineStatus;
  steps: AgentStep[];
  outputs: PipelineOutputs;
  error: string | null;
}

function initialSteps(): AgentStep[] {
  return AGENT_ORDER.map((name) => ({ name, status: 'pending' as const }));
}

export function usePipeline() {
  const [state, setState] = useState<PipelineState>({
    status: 'idle',
    steps: initialSteps(),
    outputs: {},
    error: null,
  });

  const eventSourceRef = useRef<EventSource | null>(null);

  const connectSSE = useCallback((runId: string) => {
    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = new EventSource(`/api/v1/pipeline/stream/${runId}`);
    eventSourceRef.current = es;

    es.addEventListener('status_update', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      const agentName = data.agent_name as AgentName;

      setState((prev) => ({
        ...prev,
        status: data.status as PipelineStatus,
        steps: prev.steps.map((step) => {
          if (step.name === agentName) {
            return { ...step, status: 'running', elapsedMs: data.elapsed_ms };
          }
          return step;
        }),
      }));
    });

    es.addEventListener('agent_complete', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      const agentName = data.agent_name as AgentName;

      setState((prev) => ({
        ...prev,
        steps: prev.steps.map((step) => {
          if (step.name === agentName) {
            return { ...step, status: 'complete', elapsedMs: data.elapsed_ms };
          }
          return step;
        }),
        outputs: {
          ...prev.outputs,
          [agentName]: data.output,
        },
      }));
    });

    es.addEventListener('reporter_status', (e: MessageEvent) => {
      const data = JSON.parse(e.data);

      setState((prev) => {
        const newState = { ...prev };
        if (data.status === 'reporting') {
          newState.steps = prev.steps.map((step) =>
            step.name === 'performance_reporter'
              ? { ...step, status: 'running' as const }
              : step
          );
        }
        if (data.output) {
          newState.steps = prev.steps.map((step) =>
            step.name === 'performance_reporter'
              ? { ...step, status: 'complete' as const }
              : step
          );
          newState.outputs = {
            ...prev.outputs,
            performance_reporter: data.output as PerformanceOutput,
          };
        }
        return newState;
      });
    });

    es.addEventListener('pipeline_complete', () => {
      setState((prev) => ({ ...prev, status: 'complete' }));
      es.close();
    });

    es.addEventListener('pipeline_failed', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setState((prev) => ({
        ...prev,
        status: 'failed',
        error: data.error?.message || 'Pipeline failed',
        steps: prev.steps.map((step) =>
          step.name === data.failed_agent
            ? { ...step, status: 'failed' as const }
            : step
        ),
      }));
      es.close();
    });

    es.onerror = () => {
      es.close();
    };
  }, []);

  const reset = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setState({
      status: 'idle',
      steps: initialSteps(),
      outputs: {},
      error: null,
    });
  }, []);

  const setDemoOutputs = useCallback((outputs: {
    brief_parsed: BriefParserOutput;
    audience: AudienceOutput;
    calendar: CalendarOutput;
    creative_brief: CreativeBriefOutput;
    performance: PerformanceOutput;
  }) => {
    setState({
      status: 'complete',
      steps: AGENT_ORDER.map((name) => ({ name, status: 'complete' as const })),
      outputs: {
        brief_parser: outputs.brief_parsed,
        audience_researcher: outputs.audience,
        content_calendar: outputs.calendar,
        creative_brief: outputs.creative_brief,
        performance_reporter: outputs.performance,
      },
      error: null,
    });
  }, []);

  return {
    ...state,
    connectSSE,
    reset,
    setDemoOutputs,
  };
}
