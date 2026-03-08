import { Settings as SettingsIcon } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function Settings() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8">
        <SettingsIcon className="h-16 w-16 text-primary mx-auto mb-4" />
        <h1 className="text-4xl font-bold mb-4">Settings</h1>
        <p className="text-xl text-gray-600 dark:text-gray-300">
          Configure the MCP testing environment
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Application Settings</CardTitle>
          <CardDescription>
            Configure your MCP testing preferences
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-gray-500">Settings interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  )
}