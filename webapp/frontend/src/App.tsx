import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/toaster'
import { ThemeProvider } from '@/components/theme-provider'

import Dashboard from '@/pages/Dashboard'
import DeviceTesting from '@/pages/DeviceTesting'
import ConversationalInterface from '@/pages/ConversationalInterface'
import MCPStatus from '@/pages/MCPStatus'
import Settings from '@/pages/Settings'
import Layout from '@/components/Layout'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="light" storageKey="nest-protect-theme">
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/devices" element={<DeviceTesting />} />
              <Route path="/conversational" element={<ConversationalInterface />} />
              <Route path="/status" element={<MCPStatus />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </Router>
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App