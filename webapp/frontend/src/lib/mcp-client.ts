import type {
  APIResponse,
  DeviceEvent,
  DeviceInfo,
  DeviceStatus,
  EmergencyResponse,
  MCPResponse,
  PredictiveMaintenance,
  SafetyAssessmentResult,
  WebSocketMessage,
} from "@/types/mcp";
import axios, { AxiosResponse } from "axios";
import { type Socket, io } from "socket.io-client";

class MCPClient {
  private baseURL: string;
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(baseURL = "http://localhost:7771") {
    this.baseURL = baseURL;
    this.setupAxiosInterceptors();
  }

  private setupAxiosInterceptors() {
    axios.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error("API Error:", error);
        return Promise.reject(error);
      },
    );
  }

  // Connection management
  async connect(): Promise<boolean> {
    try {
      this.socket = io(this.baseURL, {
        transports: ["websocket", "polling"],
        timeout: 5000,
      });

      return new Promise((resolve) => {
        this.socket?.on("connect", () => {
          console.log("Connected to MCP server");
          this.reconnectAttempts = 0;
          resolve(true);
        });

        this.socket?.on("connect_error", (error) => {
          console.error("Connection failed:", error);
          resolve(false);
        });

        this.socket?.on("disconnect", (reason) => {
          console.log("Disconnected:", reason);
          if (reason === "io server disconnect") {
            this.attemptReconnect();
          }
        });
      });
    } catch (error) {
      console.error("Failed to connect:", error);
      return false;
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`,
      );

      setTimeout(() => {
        this.connect();
      }, 2000 * this.reconnectAttempts); // Exponential backoff
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // WebSocket event listeners
  onMessage(callback: (message: WebSocketMessage) => void) {
    this.socket?.on("message", callback);
  }

  onDeviceUpdate(callback: (data: DeviceStatus) => void) {
    this.socket?.on("device_update", callback);
  }

  onAlarmTriggered(callback: (data: any) => void) {
    this.socket?.on("alarm_triggered", callback);
  }

  onMCPStatus(callback: (data: any) => void) {
    this.socket?.on("mcp_status", callback);
  }

  // Device management
  async listDevices(): Promise<MCPResponse & { result: { devices: DeviceInfo[] } }> {
    const response = await axios.get<APIResponse>(`${this.baseURL}/api/devices`);
    return response.data.data as MCPResponse & { result: { devices: DeviceInfo[] } };
  }

  async getDeviceStatus(
    deviceId: string,
  ): Promise<MCPResponse & { result: { device: DeviceStatus } }> {
    const response = await axios.get<APIResponse>(`${this.baseURL}/api/devices/${deviceId}`);
    return response.data.data as MCPResponse & { result: { device: DeviceStatus } };
  }

  async getDeviceEvents(
    deviceId: string,
    limit = 10,
  ): Promise<MCPResponse & { result: { events: DeviceEvent[] } }> {
    const response = await axios.get<APIResponse>(
      `${this.baseURL}/api/devices/${deviceId}/events`,
      {
        params: { limit },
      },
    );
    return response.data.data as MCPResponse & { result: { events: DeviceEvent[] } };
  }

  // Device control
  async hushAlarm(deviceId: string, durationSeconds = 180): Promise<MCPResponse> {
    const response = await axios.post<APIResponse>(`${this.baseURL}/api/devices/${deviceId}/hush`, {
      duration_seconds: durationSeconds,
    });
    return response.data.data as MCPResponse;
  }

  async runSafetyCheck(deviceId: string, testType = "full"): Promise<MCPResponse> {
    const response = await axios.post<APIResponse>(`${this.baseURL}/api/devices/${deviceId}/test`, {
      test_type: testType,
    });
    return response.data.data as MCPResponse;
  }

  async setLedBrightness(deviceId: string, brightness: number): Promise<MCPResponse> {
    const response = await axios.post<APIResponse>(
      `${this.baseURL}/api/devices/${deviceId}/brightness`,
      {
        brightness,
      },
    );
    return response.data.data as MCPResponse;
  }

  async soundAlarm(
    deviceId: string,
    alarmType = "smoke",
    durationSeconds = 10,
    volume = 100,
  ): Promise<MCPResponse> {
    const response = await axios.post<APIResponse>(
      `${this.baseURL}/api/devices/${deviceId}/alarm`,
      {
        alarm_type: alarmType,
        duration_seconds: durationSeconds,
        volume,
      },
    );
    return response.data.data as MCPResponse;
  }

  // AI Orchestration (FastMCP 2.14.3 features)
  async assessHomeSafety(
    options: {
      include_recommendations?: boolean;
      assessment_scope?: string;
      focus_areas?: string[];
    } = {},
  ): Promise<MCPResponse & { result: SafetyAssessmentResult }> {
    const response = await axios.post<APIResponse>(`${this.baseURL}/api/ai/assess-safety`, options);
    return response.data.data as MCPResponse & { result: SafetyAssessmentResult };
  }

  async coordinateEmergencyResponse(options: {
    emergency_type: string;
    affected_devices: string[];
    response_priority?: string;
  }): Promise<MCPResponse & { result: EmergencyResponse }> {
    const response = await axios.post<APIResponse>(
      `${this.baseURL}/api/ai/emergency-response`,
      options,
    );
    return response.data.data as MCPResponse & { result: EmergencyResponse };
  }

  async predictMaintenance(
    options: {
      analysis_depth?: string;
      time_horizon?: string;
      include_cost_estimates?: boolean;
    } = {},
  ): Promise<MCPResponse & { result: PredictiveMaintenance }> {
    const response = await axios.post<APIResponse>(
      `${this.baseURL}/api/ai/predict-maintenance`,
      options,
    );
    return response.data.data as MCPResponse & { result: PredictiveMaintenance };
  }

  async setupSmartAutomation(options: {
    automation_type: string;
    learning_period?: string;
    confidence_threshold?: number;
  }): Promise<MCPResponse> {
    const response = await axios.post<APIResponse>(
      `${this.baseURL}/api/ai/smart-automation`,
      options,
    );
    return response.data.data as MCPResponse;
  }

  // System management
  async getSystemStatus(): Promise<MCPResponse> {
    const response = await axios.get<APIResponse>(`${this.baseURL}/api/system/status`);
    return response.data.data as MCPResponse;
  }

  async getMCPStatus(): Promise<MCPResponse> {
    const response = await axios.get<APIResponse>(`${this.baseURL}/api/mcp/status`);
    return response.data.data as MCPResponse;
  }

  async getAvailableTools(): Promise<MCPResponse & { result: { tools: any[] } }> {
    const response = await axios.get<APIResponse>(`${this.baseURL}/api/mcp/tools`);
    return response.data.data as MCPResponse & { result: { tools: any[] } };
  }

  // Authentication
  async initiateOAuthFlow(): Promise<MCPResponse> {
    const response = await axios.post<APIResponse>(`${this.baseURL}/api/auth/initiate`);
    return response.data.data as MCPResponse;
  }

  async refreshAccessToken(): Promise<MCPResponse> {
    const response = await axios.post<APIResponse>(`${this.baseURL}/api/auth/refresh`);
    return response.data.data as MCPResponse;
  }

  // Configuration
  async getConfig(): Promise<MCPResponse> {
    const response = await axios.get<APIResponse>(`${this.baseURL}/api/config`);
    return response.data.data as MCPResponse;
  }

  async updateConfig(updates: Record<string, any>): Promise<MCPResponse> {
    const response = await axios.post<APIResponse>(`${this.baseURL}/api/config`, updates);
    return response.data.data as MCPResponse;
  }

  // Utility methods
  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  getConnectionStatus(): { connected: boolean; reconnectAttempts: number } {
    return {
      connected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
    };
  }
}

// Export singleton instance
export const mcpClient = new MCPClient();
export default MCPClient;
