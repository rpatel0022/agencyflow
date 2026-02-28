// Typed API client functions

import type { DemoResponse } from '../types/pipeline';

interface RunPipelineResponse {
  run_id: string;
  status: string;
}

export async function startPipeline(text: string): Promise<RunPipelineResponse> {
  const formData = new FormData();
  formData.append('text', text);

  const response = await fetch('/api/v1/pipeline/run', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function startPipelineWithFile(file: File): Promise<RunPipelineResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/v1/pipeline/run', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function fetchDemo(): Promise<DemoResponse> {
  const response = await fetch('/api/v1/pipeline/demo', { method: 'POST' });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}
