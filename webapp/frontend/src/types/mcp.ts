// Types for MCP (Model Context Protocol) responses and data structures

export interface MCPResponse {
  success: boolean
  operation?: string
  summary?: string
  result?: any
  requires_sampling?: boolean
  sampling_reason?: string
  next_steps?: string[]
  context?: Record<string, any>
  suggestions?: string[]
  follow_up_questions?: string[]
  error?: string
  error_code?: string
  message?: string
  recovery_options?: string[]
  diagnostic_info?: Record<string, any>
  estimated_resolution_time?: string
  urgency?: 'low' | 'medium' | 'high' | 'critical'
}

export interface DeviceInfo {
  id: string
  name: string
  model: string
  type: string
  online: boolean
  last_seen?: string
}

export interface DeviceStatus extends DeviceInfo {
  battery?: {
    level: number
    status: string
  }
  alarm?: {
    status: string
    last_event?: string
  }
  smoke?: {
    status: string
    last_event?: string
  }
  co?: {
    status: string
    level_ppm?: number
    last_event?: string
  }
  heat?: {
    status: string
    temperature_c?: number
    humidity?: number
  }
  location?: string
  last_update?: string
}

export interface DeviceEvent {
  event_id: string
  type: string
  timestamp: string
  data: Record<string, any>
}

export interface SafetyAssessmentResult {
  assessment_scope: string
  devices_analyzed: number
  safety_issues: Array<{
    type: string
    device: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    description: string
  }>
  analysis: {
    total_devices: number
    online_count: number
    critical_issues: number
    recommendations_count: number
  }
}

export interface MCPTool {
  name: string
  description: string
  parameters?: Record<string, any>
}

export interface MCPServerStatus {
  connected: boolean
  version?: string
  tools_count?: number
  last_ping?: string
  error?: string
}

export interface ConversationMessage {
  id: string
  timestamp: string
  type: 'user' | 'assistant' | 'system' | 'error'
  content: string
  metadata?: Record<string, any>
}

export interface TestResult {
  test_name: string
  status: 'pending' | 'running' | 'passed' | 'failed'
  duration?: number
  error?: string
  result?: any
}

export interface EmergencyResponse {
  emergency_type: 'smoke' | 'co' | 'security' | 'medical' | 'unknown'
  affected_devices: string[]
  response_priority: 'low' | 'medium' | 'high' | 'critical'
  coordination_status: string
  estimated_response_time?: string
}

export interface PredictiveMaintenance {
  analysis_depth: 'quick' | 'detailed' | 'comprehensive'
  time_horizon: '1_week' | '1_month' | '3_months' | '1_year'
  predictions_generated: boolean
  estimated_cost_savings?: number
  recommended_actions?: string[]
}

// WebSocket message types for real-time updates
export interface WebSocketMessage {
  type: 'device_update' | 'alarm_triggered' | 'mcp_status' | 'test_result' | 'conversation_update'
  payload: any
  timestamp: string
}

// API response types
export interface APIResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// Form types for user inputs
export interface DeviceTestForm {
  device_id: string
  test_type: 'smoke' | 'co' | 'full' | 'connectivity'
  duration_seconds?: number
}

export interface AlarmControlForm {
  device_id: string
  action: 'hush' | 'test'
  duration_seconds?: number
  test_type?: string
}

export interface SettingsForm {
  mcp_server_url: string
  auto_refresh: boolean
  refresh_interval: number
  theme: 'light' | 'dark' | 'system'
  notifications: boolean
}