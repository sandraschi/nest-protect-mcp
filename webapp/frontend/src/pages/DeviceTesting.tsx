import { useState, useEffect } from 'react'
import { TestTube, Shield, Wifi, Battery, Thermometer, AlertTriangle, CheckCircle, Play } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { mcpClient } from '@/lib/mcp-client'
import { DeviceInfo, DeviceStatus, MCPResponse } from '@/types/mcp'

export default function DeviceTesting() {
  const [devices, setDevices] = useState<DeviceInfo[]>([])
  const [selectedDevice, setSelectedDevice] = useState<string>('')
  const [isLoading, setIsLoading] = useState(false)
  const [testResults, setTestResults] = useState<Record<string, any>>({})
  const [deviceStatus, setDeviceStatus] = useState<DeviceStatus | null>(null)

  useEffect(() => {
    loadDevices()
  }, [])

  const loadDevices = async () => {
    try {
      setIsLoading(true)
      const response = await mcpClient.listDevices()
      if (response.success && response.result) {
        setDevices(response.result.devices)
      }
    } catch (error) {
      console.error('Failed to load devices:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const loadDeviceStatus = async (deviceId: string) => {
    try {
      const response = await mcpClient.getDeviceStatus(deviceId)
      if (response.success && response.result) {
        setDeviceStatus(response.result.device)
      }
    } catch (error) {
      console.error('Failed to load device status:', error)
    }
  }

  const runSafetyTest = async (deviceId: string, testType: string = 'full') => {
    try {
      setTestResults(prev => ({ ...prev, [deviceId]: { status: 'running', testType } }))

      const response = await mcpClient.runSafetyCheck(deviceId, testType)

      setTestResults(prev => ({
        ...prev,
        [deviceId]: {
          status: response.success ? 'completed' : 'failed',
          testType,
          result: response,
          timestamp: new Date().toISOString()
        }
      }))

      // Refresh device status after test
      if (selectedDevice === deviceId) {
        await loadDeviceStatus(deviceId)
      }

    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [deviceId]: {
          status: 'failed',
          testType,
          error: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date().toISOString()
        }
      }))
    }
  }

  const hushAlarm = async (deviceId: string) => {
    try {
      const response = await mcpClient.hushAlarm(deviceId, 180)
      if (response.success) {
        alert('Alarm hushed successfully for 3 minutes')
        await loadDeviceStatus(deviceId)
      }
    } catch (error) {
      alert('Failed to hush alarm')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'OK':
      case 'ONLINE':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'LOW':
      case 'OFFLINE':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-red-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OK':
      case 'ONLINE':
        return 'text-green-600'
      case 'LOW':
      case 'OFFLINE':
        return 'text-yellow-600'
      default:
        return 'text-red-600'
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-center mb-6">
          <div className="relative">
            <TestTube className="h-16 w-16 text-primary animate-pulse" />
            <div className="absolute -top-2 -right-2 h-6 w-6 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center">
              <Shield className="h-3 w-3 text-white" />
            </div>
          </div>
        </div>

        <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent text-center mb-4">
          Device Testing Suite
        </h1>

        <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto text-center mb-8">
          Comprehensive testing interface for Nest Protect devices with real-time monitoring,
          safety diagnostics, and interactive controls.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Device List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="h-5 w-5 mr-2" />
                Devices ({devices.length})
              </CardTitle>
              <CardDescription>
                Available Nest Protect devices
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="text-sm text-gray-500 mt-2">Loading devices...</p>
                </div>
              ) : devices.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No devices found</p>
                  <p className="text-sm">Check MCP server connection</p>
                </div>
              ) : (
                devices.map((device) => (
                  <div
                    key={device.id}
                    onClick={() => {
                      setSelectedDevice(device.id)
                      loadDeviceStatus(device.id)
                    }}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedDevice === device.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{device.name || `Device ${device.id.slice(-4)}`}</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">{device.type}</div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(device.online ? 'ONLINE' : 'OFFLINE')}
                        <Badge variant={device.online ? 'success' : 'destructive'} className="text-xs">
                          {device.online ? 'Online' : 'Offline'}
                        </Badge>
                      </div>
                    </div>

                    {/* Test Status */}
                    {testResults[device.id] && (
                      <div className="mt-2 flex items-center space-x-2">
                        <Badge
                          variant={
                            testResults[device.id].status === 'completed' ? 'success' :
                            testResults[device.id].status === 'running' ? 'warning' : 'destructive'
                          }
                          className="text-xs"
                        >
                          {testResults[device.id].status}
                        </Badge>
                        {testResults[device.id].testType && (
                          <span className="text-xs text-gray-500">
                            {testResults[device.id].testType} test
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Device Details & Controls */}
        <div className="lg:col-span-2">
          {selectedDevice && deviceStatus ? (
            <div className="space-y-6">
              {/* Device Status Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Wifi className="h-5 w-5 mr-2" />
                    {deviceStatus.name || `Device ${selectedDevice.slice(-4)}`}
                  </CardTitle>
                  <CardDescription>
                    Device ID: {selectedDevice}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${getStatusColor(deviceStatus.online ? 'ONLINE' : 'OFFLINE')}`}>
                        {deviceStatus.online ? '●' : '○'}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Status</div>
                    </div>

                    {deviceStatus.battery && (
                      <div className="text-center">
                        <Battery className={`h-6 w-6 mx-auto mb-1 ${getStatusColor(deviceStatus.battery.status)}`} />
                        <div className="text-lg font-bold">{deviceStatus.battery.level}%</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Battery</div>
                      </div>
                    )}

                    {deviceStatus.alarm && (
                      <div className="text-center">
                        <AlertTriangle className={`h-6 w-6 mx-auto mb-1 ${getStatusColor(deviceStatus.alarm.status === 'NONE' ? 'OK' : 'ALARM')}`} />
                        <div className="text-sm font-medium">{deviceStatus.alarm.status}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Alarm</div>
                      </div>
                    )}

                    {deviceStatus.heat && deviceStatus.temperature_c && (
                      <div className="text-center">
                        <Thermometer className="h-6 w-6 mx-auto mb-1 text-blue-500" />
                        <div className="text-lg font-bold">{deviceStatus.temperature_c}°C</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Temperature</div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Test Controls */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <TestTube className="h-5 w-5 mr-2" />
                    Safety Testing
                  </CardTitle>
                  <CardDescription>
                    Run comprehensive safety tests on this device
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <Button
                      onClick={() => runSafetyTest(selectedDevice, 'full')}
                      disabled={testResults[selectedDevice]?.status === 'running'}
                      className="flex flex-col h-auto py-4"
                    >
                      <Play className="h-4 w-4 mb-1" />
                      Full Test
                    </Button>

                    <Button
                      onClick={() => runSafetyTest(selectedDevice, 'smoke')}
                      disabled={testResults[selectedDevice]?.status === 'running'}
                      variant="outline"
                      className="flex flex-col h-auto py-4"
                    >
                      <Shield className="h-4 w-4 mb-1" />
                      Smoke
                    </Button>

                    <Button
                      onClick={() => runSafetyTest(selectedDevice, 'co')}
                      disabled={testResults[selectedDevice]?.status === 'running'}
                      variant="outline"
                      className="flex flex-col h-auto py-4"
                    >
                      <AlertTriangle className="h-4 w-4 mb-1" />
                      CO
                    </Button>

                    {deviceStatus.alarm && deviceStatus.alarm.status !== 'NONE' && (
                      <Button
                        onClick={() => hushAlarm(selectedDevice)}
                        variant="destructive"
                        className="flex flex-col h-auto py-4"
                      >
                        🔇 Hush Alarm
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Test Results */}
              {testResults[selectedDevice] && (
                <Card>
                  <CardHeader>
                    <CardTitle>Test Results</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Badge variant={
                          testResults[selectedDevice].status === 'completed' ? 'success' :
                          testResults[selectedDevice].status === 'running' ? 'warning' : 'destructive'
                        }>
                          {testResults[selectedDevice].status}
                        </Badge>
                        <span className="text-sm text-gray-600">
                          {testResults[selectedDevice].testType} test • {new Date(testResults[selectedDevice].timestamp).toLocaleTimeString()}
                        </span>
                      </div>

                      {testResults[selectedDevice].result && (
                        <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                          <div className="text-sm font-medium">{testResults[selectedDevice].result.summary}</div>
                          {testResults[selectedDevice].result.next_steps && (
                            <div className="text-xs text-gray-600 mt-1">
                              Next: {testResults[selectedDevice].result.next_steps[0]}
                            </div>
                          )}
                        </div>
                      )}

                      {testResults[selectedDevice].error && (
                        <div className="bg-red-50 dark:bg-red-950 p-3 rounded-lg">
                          <div className="text-sm text-red-800 dark:text-red-200">
                            {testResults[selectedDevice].error}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card className="h-96 flex items-center justify-center">
              <div className="text-center text-gray-500 dark:text-gray-400">
                <TestTube className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">Select a Device</h3>
                <p>Choose a device from the list to view details and run tests</p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}