import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Shield,
  Home,
  TestTube,
  MessageSquare,
  Activity,
  Settings,
  Menu,
  X,
  Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useTheme } from '@/components/theme-provider'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Device Testing', href: '/devices', icon: TestTube },
  { name: 'Conversational AI', href: '/conversational', icon: MessageSquare },
  { name: 'MCP Status', href: '/status', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
]

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const { theme, setTheme } = useTheme()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Mobile menu button */}
      <div className="fixed top-4 left-4 z-40 lg:hidden">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSidebarOpen(true)}
          className="bg-white/80 backdrop-blur-sm border-gray-200 dark:bg-slate-800/80 dark:border-slate-700"
        >
          <Menu className="h-4 w-4" />
        </Button>
      </div>

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-30 w-64 bg-white/95 backdrop-blur-sm shadow-xl transform transition-transform duration-300 ease-in-out dark:bg-slate-900/95 lg:translate-x-0 lg:static lg:inset-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-center h-16 px-4 border-b border-gray-200 dark:border-slate-700">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Shield className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              <div className="absolute -top-1 -right-1 h-3 w-3 bg-green-500 rounded-full animate-pulse"></div>
            </div>
            <div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">Nest Protect</span>
              <div className="text-xs text-gray-500 dark:text-gray-400">MCP Testing Suite</div>
            </div>
          </div>
        </div>

        <nav className="mt-8 px-4">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg mb-2 transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-500 dark:bg-blue-900/50 dark:text-blue-300'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-slate-800'
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className={`h-5 w-5 mr-3 ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`} />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* Status section */}
        <div className="mt-auto p-4 border-t border-gray-200 dark:border-slate-700">
          <div className="flex items-center space-x-2 mb-3">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">MCP Server</span>
            <Badge variant="success" className="text-xs">Connected</Badge>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            FastMCP 2.14.3 • AI Orchestration Enabled
          </div>
        </div>
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Main content */}
      <div className="lg:ml-64">
        <main className="min-h-screen">
          {children}
        </main>
      </div>
    </div>
  )
}