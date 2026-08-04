# JARVIS AI Operating System

An advanced AI assistant inspired by Tony Stark's JARVIS from the Marvel Universe. This system combines natural language processing, voice interaction, computer control, and intelligent automation to create a comprehensive personal AI operating system.

## Features

- **Natural Language Understanding**: Advanced NLP capabilities for understanding and responding to user queries
- **Voice Interaction**: Speech-to-text and text-to-speech capabilities for hands-free operation
- **Visual Interface**: Futuristic 3D interface with real-time system monitoring
- **Computer Control**: Full control over system operations, file management, and application launching
- **Automation**: Task automation and macro recording capabilities
- **Memory System**: Short-term and long-term memory for personalized interactions
- **Multi-Agent System**: Specialized agents for different tasks (coding, research, security, system administration)
- **Model Routing**: Intelligent selection of AI models based on task requirements

## Architecture

### Backend (Python)
- **Core**: Main brain orchestrating all components
- **Agents**: Specialized agents for different domains:
  - Main Agent: Conversational interface
  - Coding Agent: Software development assistance
  - Research Agent: Information gathering and analysis
  - Security Agent: Cybersecurity and threat analysis
  - System Agent: System administration and control
- **Memory**: 
  - Short-term: SQLite for recent interactions
  - Long-term: ChromaDB for semantic memory storage
- **Models**: Integration with Ollama for local LLM inference
- **Tools**: File system, terminal, browser automation, system monitoring

### Frontend (Next.js/React)
- **Interface**: Futuristic HUD with 3D avatar and visualizations
- **Components**:
  - JARVIS Orb: Visual indicator of system state
  - Chat Interface: Conversational interface with message history
  - Voice Visualizer: Audio feedback for voice interactions
  - System Panel: Real-time system metrics display
  - 3D Avatar: Interactive JARVIS representation
- **State Management**: Context-based state sharing
- **Styling**: Tailwind CSS with dark/light mode support

## Technology Stack

### Backend
- **Language**: Python 3.12+
- **Framework**: FastAPI
- **AI/ML**: 
  - Ollama (Llama 2, Mistral, etc.)
  - Sentence Transformers (for embeddings)
  - ChromaDB (vector database)
- **Audio**: 
  - Whisper (Speech-to-Text)
  - Piper (Text-to-Speech)
- **System**: 
  - PSUtil (system monitoring)
  - PyAutoGUI (GUI automation)
  - OpenCV (computer vision)
- **Communication**: 
  - WebSocket (real-time updates)
  - REST API

### Frontend
- **Framework**: Next.js 13+ (React 18)
- **Styling**: Tailwind CSS
- **3D Graphics**: Three.js with React Fiber
- **State Management**: React Context
- **HTTP Client**: Axios/SWR
- **Real-time**: Socket.IO

## Installation

### Prerequisites
- Python 3.12+
- Node.js 18+
- Ollama (for local LLM models)
- Git

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/jarvis-ai-os.git
cd jarvis-ai-os

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Pull required Ollama models
ollama pull llama2
ollama pull mistral
ollama pull codellama

# Start the backend
cd backend
python main.py
```

### Frontend Setup
```bash
# Install Node.js dependencies
cd frontend
npm install

# Start the development server
npm run dev
```

### Production Build
```bash
# Build frontend
npm run build

# Start production server
npm start
```

## Usage

1. Start both backend and frontend servers
2. Open your browser to `http://localhost:3000`
3. Click the microphone icon or press the voice button to interact with JARVIS via voice
4. Alternatively, type your queries in the chat interface
5. Use the system panel to monitor resource usage
6. Interact with the 3D avatar for additional controls

## Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=120

# Model Configuration
DEFAULT_MODEL=llama2
CODER_MODEL=codellama
REASONING_MODEL=mistral

# Memory Configuration
SQLITE_DB_PATH=./database/jarvis_memory.db
CHROMA_DB_PATH=./database/chroma_db
CHROMA_COLLECTION_NAME=jarvis_knowledge

# Voice Settings
SPEECH_RECOGNITION_MODEL=base
TTS_VOICE=en_US-lessac-medium
TTS_SPEED=1.0
TTS_VOLUME=1.0

# System Settings
MAX_CONCURRENT_TASKS=5
TASK_TIMEOUT=300
AUTO_SAVE_INTERVAL=300

# Security Settings
ENABLE_CONFIRMATION_PROMPTS=True
ALLOWED_COMMANDS=ls,dir,cat,type,echo,mkdir,rmdir,copy,xcopy,del,erase,ren,rename
BLOCKED_COMMANDS=format,del *,erase *,rmdir /s,rd /s,shutdown,restart,del /f,erase /f

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/jarvis.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
```

## Security Features

- **Local-First Design**: All processing happens locally by default
- **Command Whitelisting**: Only approved system commands can be executed
- **Confirmation Prompts**: Critical actions require user confirmation
- **Activity Logging**: All actions are logged for audit purposes
- **Sandboxed Execution**: Potentially dangerous operations are restricted

## Extending JARVIS

### Adding New Capabilities
1. Create a new agent in `backend/agents/`
2. Register the agent in the Swarm Manager
3. Define the agent's capabilities and specializations
4. Implement the agent's processing logic
5. Add any required tools or integrations

### Adding New Tools
1. Create a new module in `backend/tools/`
2. Implement the tool's functionality
3. Export the tool for use by agents
4. Document the tool's API and usage

### Customizing the Interface
1. Modify components in `frontend/components/`
2. Update styles in `app/globals.css` or `tailwind.config.js`
3. Add new pages in `app/` directory
4. Update context providers as needed

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by JARVIS from the Marvel Cinematic Universe
- Built with open-source technologies including:
  - Ollama for local LLM inference
  - Whisper for speech recognition
  - Piper for text-to-speech
  - Next.js for the frontend framework
  - FastAPI for the backend API
  - ChromaDB for vector storage
  - Three.js for 3D visualization

---

"JARVIS, initiate protocol: Iron Legion."