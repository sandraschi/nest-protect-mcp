import { useState, useEffect } from 'react'
import { Send, MessageSquare, Cpu, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { mcpClient } from '@/lib/mcp-client'
import { MCPResponse } from '@/types/mcp'

interface ConversationMessage {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
  metadata?: any
}

export default function ConversationalInterface() {
  const [messages, setMessages] = useState<ConversationMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedTool, setSelectedTool] = useState<string>('assess_home_safety')

  const quickActions = [
    {
      name: 'Safety Assessment',
      tool: 'assess_home_safety',
      description: 'AI-powered home safety evaluation',
      icon: Shield,
      color: 'bg-green-500'
    },
    {
      name: 'Emergency Response',
      tool: 'coordinate_emergency_response',
      description: 'Coordinate emergency handling',
      icon: AlertTriangle,
      color: 'bg-red-500'
    },
    {
      name: 'Predictive Maintenance',
      tool: 'predict_maintenance_needs',
      description: 'AI maintenance forecasting',
      icon: TrendingUp,
      color: 'bg-blue-500'
    },
    {
      name: 'Smart Automation',
      tool: 'setup_smart_automation',
      description: 'Intelligent automation setup',
      icon: Cpu,
      color: 'bg-purple-500'
    }
  ]

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: ConversationMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      let response: MCPResponse

      // Simulate tool calls based on input
      if (inputMessage.toLowerCase().includes('safety') || inputMessage.toLowerCase().includes('assess')) {
        response = await mcpClient.assessHomeSafety()
      } else if (inputMessage.toLowerCase().includes('emergency') || inputMessage.toLowerCase().includes('alarm')) {
        response = await mcpClient.coordinateEmergencyResponse(
          'smoke',
          ['device-001'],
          'high'
        )
      } else if (inputMessage.toLowerCase().includes('maintenance') || inputMessage.toLowerCase().includes('predict')) {
        response = await mcpClient.predictMaintenance()
      } else {
        // Default to safety assessment
        response = await mcpClient.assessHomeSafety()
      }

      const assistantMessage: ConversationMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.summary || 'Response received',
        timestamp: new Date().toISOString(),
        metadata: {
          operation: response.operation,
          success: response.success,
          requires_sampling: response.requires_sampling,
          next_steps: response.next_steps,
          suggestions: response.suggestions,
          follow_up_questions: response.follow_up_questions
        }
      }

      setMessages(prev => [...prev, assistantMessage])

    } catch (error) {
      const errorMessage: ConversationMessage = {
        id: (Date.now() + 2).toString(),
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickAction = async (toolName: string) => {
    let response: MCPResponse

    switch (toolName) {
      case 'assess_home_safety':
        response = await mcpClient.assessHomeSafety()
        break
      case 'coordinate_emergency_response':
        response = await mcpClient.coordinateEmergencyResponse(
          'smoke',
          ['device-001', 'device-002'],
          'critical'
        )
        break
      case 'predict_maintenance_needs':
        response = await mcpClient.predictMaintenance()
        break
      case 'setup_smart_automation':
        response = await mcpClient.setupSmartAutomation('safety')
        break
      default:
        return
    }

    const message: ConversationMessage = {
      id: Date.now().toString(),
      type: 'assistant',
      content: response.summary || `${toolName} executed`,
      timestamp: new Date().toISOString(),
      metadata: {
        operation: response.operation,
        success: response.success,
        requires_sampling: response.requires_sampling,
        next_steps: response.next_steps,
        suggestions: response.suggestions,
        follow_up_questions: response.follow_up_questions
      }
    }

    setMessages(prev => [...prev, message])
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-center mb-6">
          <div className="relative">
            <MessageSquare className="h-16 w-16 text-primary animate-pulse" />
            <div className="absolute -top-2 -right-2 h-6 w-6 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
              <Zap className="h-3 w-3 text-white" />
            </div>
          </div>
        </div>

        <h1 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent text-center mb-4">
          Conversational AI Interface
        </h1>

        <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto text-center mb-8">
          Experience FastMCP 2.14.3 conversational responses with intelligent suggestions,
          sampling signals, and natural language interactions.
        </p>

        {/* Feature Badges */}
        <div className="flex flex-wrap justify-center gap-3 mb-8">
          <Badge variant="info" className="px-3 py-1">Conversational AI</Badge>
          <Badge variant="success" className="px-3 py-1">Sampling Signals</Badge>
          <Badge variant="warning" className="px-3 py-1">FastMCP 2.14.3</Badge>
          <Badge variant="secondary" className="px-3 py-1">AI Orchestration</Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Quick Actions Sidebar */}
        <div className="lg:col-span-1">
          <Card className="sticky top-4">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Cpu className="h-5 w-5 mr-2" />
                AI Tools
              </CardTitle>
              <CardDescription>
                FastMCP 2.14.3 intelligent operations
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {quickActions.map((action) => (
                <Button
                  key={action.tool}
                  onClick={() => handleQuickAction(action.tool)}
                  disabled={isLoading}
                  className="w-full justify-start h-auto p-4"
                  variant="outline"
                >
                  <div className="flex items-center space-x-3 w-full">
                    <div className={`p-2 rounded-lg ${action.color}`}>
                      <action.icon className="h-4 w-4 text-white" />
                    </div>
                    <div className="text-left">
                      <div className="font-medium">{action.name}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {action.description}
                      </div>
                    </div>
                  </div>
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Main Chat Interface */}
        <div className="lg:col-span-2">
          <Card className="h-[600px] flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center">
                <MessageSquare className="h-5 w-5 mr-2" />
                Conversation
              </CardTitle>
              <CardDescription>
                Interactive dialogue with AI-powered MCP responses
              </CardDescription>
            </CardHeader>

            {/* Messages Area */}
            <CardContent className="flex-1 overflow-y-auto space-y-4 p-4">
              {messages.length === 0 && (
                <div className="text-center text-gray-500 dark:text-gray-400 py-12">
                  <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Start a conversation by typing a message or using the AI tools</p>
                </div>
              )}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      message.type === 'user'
                        ? 'bg-blue-500 text-white'
                        : message.type === 'system'
                        ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                    }`}
                  >
                    <div className="text-sm">{message.content}</div>

                    {/* Metadata for assistant messages */}
                    {message.type === 'assistant' && message.metadata && (
                      <div className="mt-2 space-y-1">
                        {message.metadata.operation && (
                          <Badge variant="outline" className="text-xs">
                            {message.metadata.operation}
                          </Badge>
                        )}
                        {message.metadata.requires_sampling && (
                          <Badge variant="warning" className="text-xs ml-1">
                            Sampling Required
                          </Badge>
                        )}
                        {message.metadata.next_steps && message.metadata.next_steps.length > 0 && (
                          <div className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                            <div className="font-medium">Next steps:</div>
                            <ul className="list-disc list-inside ml-2">
                              {message.metadata.next_steps.slice(0, 2).map((step: string, idx: number) => (
                                <li key={idx}>{step}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    <div className="text-xs opacity-70 mt-1">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3 max-w-[80%]">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-sm text-gray-600 dark:text-gray-400">AI is processing...</span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>

            {/* Input Area */}
            <div className="border-t p-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                  placeholder="Type your message or use AI tools above..."
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
                  disabled={isLoading}
                />
                <Button
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  size="icon"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}