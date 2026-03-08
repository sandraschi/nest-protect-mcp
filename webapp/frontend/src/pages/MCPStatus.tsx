import { Activity, CheckCircle, XCircle, Clock } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export default function MCPStatus() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8">
        <Activity className="h-16 w-16 text-primary mx-auto mb-4" />
        <h1 className="text-4xl font-bold mb-4">MCP Server Status</h1>
        <p className="text-xl text-gray-600 dark:text-gray-300">
          Monitor the FastMCP 2.14.3 server and connection status
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="h-5 w-5 mr-2 text-green-500" />
              Server Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span>MCP Server</span>
                <Badge variant="success">Running</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Version</span>
                <Badge variant="info">2.14.3</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Tools</span>
                <Badge>20 available</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="h-5 w-5 mr-2" />
              Connection Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span>WebSocket</span>
                <Badge variant="success">Connected</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>API</span>
                <Badge variant="success">Healthy</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Devices</span>
                <Badge variant="info">0 detected</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}