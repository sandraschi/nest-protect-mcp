import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield,
  TestTube,
  MessageSquare,
  Activity,
  Zap,
  CheckCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  Cpu,
  Wifi
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { mcpClient } from '@/lib/mcp-client'
import { MCPResponse, DeviceInfo } from '@/types/mcp'

const quickActions = [
  {
    title: 'Device Testing Suite',
    description: 'Comprehensive testing of all Nest Protect devices',
    icon: TestTube,
    link: '/devices',
    color: 'bg-blue-500 hover:bg-blue-600',
    features: ['Real-time status', 'Safety checks', 'Alarm testing']
  },
  {
    title: 'Conversational AI',
    description: 'Experience FastMCP 2.14.3 conversational responses',
    icon: MessageSquare,
    link: '/conversational',
    color: 'bg-purple-500 hover:bg-purple-600',
    features: ['Natural language', 'AI recommendations', 'Sampling signals']
  },
  {
    title: 'AI Orchestration',
    description: 'Advanced AI-powered safety intelligence',
    icon: Cpu,
    link: '/conversational',
    color: 'bg-green-500 hover:bg-green-600',
    features: ['Safety assessment', 'Emergency coordination', 'Predictive maintenance']
  },
  {
    title: 'System Status',
    description: 'Monitor MCP server and device connectivity',
    icon: Activity,
    link: '/status',
    color: 'bg-orange-500 hover:bg-orange-600',
    features: ['Real-time monitoring', 'Connection status', 'Performance metrics']
  }
]

export default function Dashboard() {
  const [serverStatus, setServerStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting')
  const [deviceCount, setDeviceCount] = useState(0)
  const [lastUpdate, setLastUpdate] = useState<string>('')

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const connected = await mcpClient.connect()
        setServerStatus(connected ? 'connected' : 'disconnected')

        if (connected) {
          const response = await mcpClient.listDevices()
          if (response.success && response.result) {
            setDeviceCount(response.result.devices.length)
          }
        }
      } catch (error) {
        setServerStatus('disconnected')
      }
      setLastUpdate(new Date().toLocaleTimeString())
    }

    checkStatus()
    const interval = setInterval(checkStatus, 30000) // Check every 30 seconds

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-center mb-6">
          <div className="relative">
            <Shield className="h-16 w-16 text-primary animate-pulse" />
            <div className="absolute -top-2 -right-2 h-6 w-6 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
              <Zap className="h-3 w-3 text-white" />
            </div>
          </div>
        </div>

        <h1 className="text-4xl lg:text-6xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent text-center mb-4">
          Nest Protect MCP
        </h1>

        <p className="text-xl lg:text-2xl text-gray-600 dark:text-gray-300 max-w-4xl mx-auto text-center mb-8 leading-relaxed">
          FastMCP 2.14.3 Testing Suite - Experience conversational AI, sampling capabilities,
          and intelligent device orchestration for next-generation smart home safety.
        </p>

        {/* Status Banner */}
        <div className="flex items-center justify-center mb-8">
          <Card className="border-2 border-dashed border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/50">
            <CardContent className="p-4">
              <div className="flex items-center space-x-4">
                <div className={`w-3 h-3 rounded-full ${
                  serverStatus === 'connected' ? 'bg-green-500 animate-pulse' :
                  serverStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                  'bg-red-500'
                }`}></div>
                <div className="flex items-center space-x-2">
                  <span className="font-medium">MCP Server:</span>
                  <Badge variant={serverStatus === 'connected' ? 'success' : 'destructive'}>
                    {serverStatus === 'connected' ? 'Connected' :
                     serverStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
                  </Badge>
                </div>
                {deviceCount > 0 && (
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">Devices:</span>
                    <Badge variant="info">{deviceCount} detected</Badge>
                  </div>
                )}
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Last updated: {lastUpdate}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-12">
        <h2 className="text-3xl font-bold text-center mb-8 text-gray-900 dark:text-white">
          Testing Capabilities
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions.map((action, index) => (
            <Card key={index} className="hover:shadow-xl transition-all duration-300 hover:scale-105 cursor-pointer group">
              <CardContent className="p-6">
                <div className="flex items-center justify-center mb-4">
                  <div className={`p-3 rounded-full ${action.color} group-hover:scale-110 transition-transform duration-300`}>
                    <action.icon className="h-8 w-8 text-white" />
                  </div>
                </div>
                <h3 className="text-xl font-semibold text-center mb-2">{action.title}</h3>
                <p className="text-gray-600 dark:text-gray-300 text-center mb-4 text-sm">{action.description}</p>

                <div className="space-y-1 mb-4">
                  {action.features.map((feature, idx) => (
                    <div key={idx} className="flex items-center text-xs text-gray-500 dark:text-gray-400">
                      <CheckCircle className="h-3 w-3 text-green-500 mr-2" />
                      {feature}
                    </div>
                  ))}
                </div>

                <Button asChild className="w-full">
                  <Link to={action.link}>
                    Open {action.title}
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Feature Highlights */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <Card className="text-center border-0 shadow-lg bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900">
          <CardContent className="p-6">
            <MessageSquare className="h-12 w-12 text-blue-600 dark:text-blue-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-blue-800 dark:text-blue-200 mb-2">Conversational AI</h3>
            <p className="text-blue-700 dark:text-blue-300 text-sm">
              Experience natural language responses with contextual suggestions and follow-up questions
            </p>
          </CardContent>
        </Card>

        <Card className="text-center border-0 shadow-lg bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900">
          <CardContent className="p-6">
            <Cpu className="h-12 w-12 text-purple-600 dark:text-purple-400 mx-auto mb-4" />
            <div className="flex items-center justify-center mb-2">
              <span className="text-lg font-semibold text-purple-800 dark:text-purple-200 mr-2">Sampling</span>
              <Badge variant="info" className="text-xs">FastMCP 2.14.3</Badge>
            </div>
            <p className="text-purple-700 dark:text-purple-300 text-sm">
              AI reasoning signals for complex operations and intelligent orchestration
            </p>
          </CardContent>
        </Card>

        <Card className="text-center border-0 shadow-lg bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900">
          <CardContent className="p-6">
            <TrendingUp className="h-12 w-12 text-green-600 dark:text-green-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-green-800 dark:text-green-200 mb-2">AI Orchestration</h3>
            <p className="text-green-700 dark:text-green-300 text-sm">
              Intelligent device coordination with predictive maintenance and emergency response
            </p>
          </CardContent>
        </Card>
      </div>

      {/* System Overview */}
      <Card className="border-0 shadow-xl bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-900 dark:to-blue-950">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center">
            <Activity className="h-6 w-6 mr-2" />
            System Overview
          </CardTitle>
          <CardDescription>
            Current status of the Nest Protect MCP testing environment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="flex items-center space-x-3 p-4 bg-white dark:bg-slate-800 rounded-lg">
              <div className={`w-3 h-3 rounded-full ${
                serverStatus === 'connected' ? 'bg-green-500 animate-pulse' :
                serverStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
                'bg-red-500'
              }`}></div>
              <div>
                <div className="font-medium">MCP Server</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {serverStatus === 'connected' ? 'Active - FastMCP 2.14.3' :
                   serverStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-4 bg-white dark:bg-slate-800 rounded-lg">
              <Wifi className="h-5 w-5 text-blue-500" />
              <div>
                <div className="font-medium">Device Discovery</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {deviceCount > 0 ? `${deviceCount} devices detected` : 'Scanning...'}
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-4 bg-white dark:bg-slate-800 rounded-lg">
              <Shield className="h-5 w-5 text-green-500" />
              <div>
                <div className="font-medium">Safety Systems</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  AI orchestration enabled
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3 p-4 bg-white dark:bg-slate-800 rounded-lg">
              <Clock className="h-5 w-5 text-purple-500" />
              <div>
                <div className="font-medium">Last Update</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {lastUpdate || 'Initializing...'}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}