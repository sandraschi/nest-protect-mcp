# Nest Protect MCP Testing Webapp

A beautiful, modern web application for testing and demonstrating the Nest Protect MCP server with FastMCP 2.14.3 conversational AI capabilities.

## Features

### 🚀 FastMCP 2.14.3 Features
- **Conversational AI**: Natural language responses with contextual suggestions
- **Sampling Capabilities**: AI reasoning signals for complex operations
- **Advanced AI Orchestration**: Intelligent device coordination and emergency response

### 🎨 Beautiful UI
- **Modern Design**: Clean, responsive interface with dark/light theme support
- **Real-time Updates**: Live device status and test results
- **Interactive Testing**: Comprehensive device testing suite
- **Conversational Interface**: Chat-like interaction with MCP responses

### 🛠️ Testing Capabilities
- **Device Discovery**: Automatic detection of Nest Protect devices
- **Safety Testing**: Comprehensive smoke, CO, and safety diagnostics
- **Real-time Monitoring**: Live status updates and event streaming
- **Interactive Controls**: Alarm management and device configuration

## Architecture

```
webapp/
├── frontend/          # React/TypeScript frontend
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Main application pages
│   │   ├── lib/           # MCP client and utilities
│   │   └── types/         # TypeScript type definitions
│   └── package.json
└── backend/           # FastAPI backend
    ├── main.py           # Main FastAPI application
    └── requirements.txt
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- MCP server running (see main project)

### Installation

1. **Install dependencies:**
   ```bash
   cd webapp
   npm install
   pip install -r backend/requirements.txt
   ```

2. **Start the development servers:**
   ```bash
   # Start both frontend and backend
   npm run dev

   # Or start individually:
   npm run dev:frontend  # Frontend on http://localhost:7770
   npm run dev:backend   # Backend on http://localhost:7771
   ```

3. **Open your browser:**
   - Frontend: http://localhost:7770
   - Backend API: http://localhost:7771

## Pages

### Dashboard
- Overview of MCP server status
- Quick access to testing features
- System health monitoring

### Device Testing
- Discover and list all devices
- Real-time device status monitoring
- Interactive safety testing
- Alarm control and management

### Conversational AI
- Chat interface with MCP responses
- Experience conversational tool returns
- Test sampling capabilities
- AI orchestration demonstrations

### MCP Status
- Server connection monitoring
- Tool availability
- Performance metrics
- Real-time status updates

## API Endpoints

### Device Management
- `GET /api/devices` - List all devices
- `GET /api/devices/{id}` - Get device status
- `GET /api/devices/{id}/events` - Get device events
- `POST /api/devices/{id}/hush` - Hush alarm
- `POST /api/devices/{id}/test` - Run safety test

### AI Orchestration
- `POST /api/ai/assess-safety` - Comprehensive safety assessment
- `POST /api/ai/emergency-response` - Emergency coordination
- `POST /api/ai/predict-maintenance` - Predictive maintenance
- `POST /api/ai/smart-automation` - Setup smart automation

### System
- `GET /api/health` - Health check
- `GET /api/system/status` - System status
- `GET /api/mcp/status` - MCP server status

## WebSocket Events

The backend provides real-time updates via WebSocket:

```javascript
// Connect to WebSocket
const socket = io('http://localhost:7771');

// Listen for events
socket.on('device_update', (data) => {
  console.log('Device updated:', data);
});

socket.on('alarm_triggered', (data) => {
  console.log('Alarm triggered:', data);
});
```

## FastMCP 2.14.3 Features Demonstrated

### Conversational Responses
All API endpoints return conversational responses with:
- Natural language summaries
- Suggested next steps
- Contextual information
- Follow-up questions

### Sampling Capabilities
Advanced AI tools trigger sampling signals when complex reasoning is required:
- Emergency coordination
- Safety assessments
- Predictive maintenance
- Smart automation setup

### AI Orchestration
Intelligent multi-device operations:
- Emergency response coordination
- Safety assessment across all devices
- Predictive maintenance scheduling
- Adaptive automation learning

## Development

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Building for Production
```bash
npm run build
```

## Contributing

1. Follow the existing code structure
2. Use TypeScript for frontend code
3. Implement conversational responses in backend
4. Test with both mock and real devices
5. Update documentation

## License

MIT License - see LICENSE file for details.

---

**Built with ❤️ for testing FastMCP 2.14.3 conversational AI capabilities**