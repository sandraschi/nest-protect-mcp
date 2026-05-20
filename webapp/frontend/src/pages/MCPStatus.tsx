import { useEffect, useState } from 'react'
import { Activity, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { mcpClient } from '@/lib/mcp-client'

interface StatusData {
  connected: boolean
  version?: string
  tools_count?: number
  mcp_server?: string
  device_count?: number
  last_health_check?: string
}

export default function MCPStatus() {
  const [data, setData] = useState<StatusData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    (async () => {
      try {
        const [sys, mcp] = await Promise.all([
          mcpClient.getSystemStatus(),
          mcpClient.getMCPStatus(),
        ])
        setData({
          connected: (sys as { success?: boolean }).success ?? false,
          mcp_server: (sys as { result?: { mcp_server?: string } }).result?.mcp_server,
          device_count: (sys as { result?: { device_count?: number } }).result?.device_count,
          last_health_check: (sys as { result?: { last_health_check?: string } }).result?.last_health_check,
          version: (mcp as { result?: { version?: string } }).result?.version,
          tools_count: (mcp as { result?: { tools_count?: number } }).result?.tools_count,
        })
      } catch (e) {
        setError((e as Error).message)
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl text-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
        <p className="text-gray-500">Loading MCP status…</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8">
        <Activity className="h-16 w-16 text-primary mx-auto mb-4" />
        <h1 className="text-4xl font-bold mb-4">MCP Server Status</h1>
        <p className="text-xl text-gray-600 dark:text-gray-300">
          {error ? 'Failed to reach server' : `Live status from Nest Protect API`}
        </p>
      </div>

      {error && (
        <Card className="border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/50 mb-6">
          <CardContent className="p-4 text-red-700 dark:text-red-300 text-sm">{error}</CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              {data?.connected ? <CheckCircle className="h-5 w-5 mr-2 text-green-500" /> : <XCircle className="h-5 w-5 mr-2 text-red-500" />}
              Server Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span>MCP Server</span>
                <Badge variant={data?.connected ? 'success' : 'destructive'}>{data?.mcp_server ?? (data?.connected ? 'Running' : 'Offline')}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Version</span>
                <Badge variant="info">{data?.version ?? '—'}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Tools</span>
                <Badge>{data?.tools_count != null ? `${data.tools_count} available` : '—'}</Badge>
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
                <Badge variant={data?.connected ? 'success' : 'destructive'}>{data?.connected ? 'Connected' : 'Disconnected'}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Devices</span>
                <Badge variant="info">{data?.device_count != null ? `${data.device_count} detected` : '—'}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Last Update</span>
                <span className="text-xs text-gray-500">{data?.last_health_check ? new Date(data.last_health_check).toLocaleTimeString() : '—'}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
