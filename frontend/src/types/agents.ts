// Agent I/O types — mirrors backend Pydantic schemas

export interface BriefParserOutput {
  campaign_name: string;
  client_name: string;
  objectives: string[];
  target_audience: string;
  budget: string | null;
  timeline: string;
  kpis: string[];
  channels: string[];
  key_messages: string[];
  constraints: string[];
  raw_summary: string;
  missing_fields: string[];
}

export interface Persona {
  name: string;
  age_range: string;
  description: string;
  motivations: string[];
  pain_points: string[];
  preferred_channels: string[];
  content_preferences: string[];
}

export interface AudienceOutput {
  personas: Persona[];
  targeting_recommendations: string[];
  audience_size_estimate: string;
  key_insights: string[];
  suggested_tone: string;
}

export interface CalendarEntry {
  week: number;
  day: string;
  channel: string;
  content_type: string;
  topic: string;
  caption_hook: string;
  hashtags: string[];
  notes: string;
}

export interface ChannelStrategy {
  channel: string;
  strategy: string;
}

export interface CalendarOutput {
  campaign_duration: string;
  posting_frequency: string;
  entries: CalendarEntry[];
  channel_strategies: ChannelStrategy[];
  content_mix_rationale: string;
}

export interface CreativeBriefOutput {
  project_name: string;
  prepared_for: string;
  date: string;
  background: string;
  objective: string;
  target_audience_summary: string;
  key_message: string;
  supporting_messages: string[];
  tone_and_voice: string;
  visual_direction: string;
  deliverables: string[];
  timeline_summary: string;
  success_metrics: string[];
  mandatory_inclusions: string[];
}

export interface ChannelAnalysis {
  channel: string;
  performance_rating: string;
  key_metric: string;
  insight: string;
  recommendation: string;
}

export interface MetricSummary {
  metric_name: string;
  value: string;
  trend: string;
}

export interface PerformanceOutput {
  executive_summary: string;
  overall_performance: string;
  channel_analysis: ChannelAnalysis[];
  top_performing_content: string[];
  recommendations: string[];
  next_steps: string[];
  key_metrics_summary: MetricSummary[];
}
