'use client';

import { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';
import { useJarvis } from '@/context/JarvisContext';

interface ChatMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { backendUrl, backendOnline, setProcessing, isProcessing } = useJarvis();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Math.random().toString(36).substr(2, 9),
      content: input,
      isUser: true,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    const text = input;
    setInput('');
    setIsLoading(true);
    setProcessing(true);

    try {
      const response = await fetch(`${backendUrl}/api/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, modality: 'text' })
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data = await response.json();
      const botContent = data.response || 'No response received.';

      setMessages(prev => [
        ...prev,
        {
          id: Math.random().toString(36).substr(2, 9),
          content: botContent,
          isUser: false,
          timestamp: new Date().toISOString()
        }
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [
        ...prev,
        {
          id: Math.random().toString(36).substr(2, 9),
          content: `Sorry, I encountered an error processing your request. ${
            backendOnline ? '' : 'The JARVIS backend appears to be offline.'
          }`,
          isUser: false,
          timestamp: new Date().toISOString()
        }
      ]);
    } finally {
      setIsLoading(false);
      setProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-gradient-to-b from-black/40 to-transparent rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/6 bg-black/30 backdrop-blur-sm">
        <div>
          <h3 className="text-sm font-semibold text-white tracking-wider">JARVIS</h3>
          <p className="text-xs text-cyan-200/50">Interactive Assistant</p>
        </div>
        <div className="text-xs text-gray-300">
          {isProcessing ? <span className="text-amber-300">Processing...</span> : (backendOnline ? 'Connected' : 'Offline')}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-gray-400 dark:text-gray-500">
              {backendOnline
                ? 'Connected to JARVIS. Ask me anything.'
                : 'JARVIS backend offline. Waiting for connection...'}
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'} mb-2`}>
            <div
              className={`max-w-[70%] px-4 py-3 rounded-2xl shadow-lg backdrop-blur-sm ${msg.isUser ? 'bg-gradient-to-br from-jarvis-500 to-jarvis-600 text-white' : 'bg-white/5 border border-white/6 text-cyan-100'}`}
            >
              <div className="flex items-start space-x-2">
                {!msg.isUser && (
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-6 h-6 bg-jarvis-500/20 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold text-jarvis-900">J</span>
                    </div>
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium mb-1">{msg.isUser ? 'You' : 'JARVIS'}</p>
                  <div
                    className="prose prose-sm max-w-none break-words"
                    dangerouslySetInnerHTML={{ __html: marked.parse(msg.content) }}
                  />
                  <time className="text-xs text-muted-foreground mt-1 block">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </time>
                </div>
                {msg.isUser && (
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-6 h-6 bg-gray-600/20 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold text-white">U</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start mb-2">
            <div className="max-w-[70%] px-4 py-2 rounded-lg bg-white/80 dark:bg-gray-700/80 border border-gray-200 dark:border-gray-600 animate-pulse">
              <div className="h-4 w-32 bg-gray-300 rounded mb-2"></div>
              <div className="h-4 w-24 bg-gray-300 rounded"></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex items-center space-x-2 p-3 bg-gradient-to-t from-black/30 to-transparent backdrop-blur border-t border-white/6">
        <button
          onClick={() => {}}
          className="p-2 rounded-full hover:bg-white/5 transition-colors"
          aria-label="Voice input"
          title="Voice input (not connected)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-cyan-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3M6 6l10.293 10.293-1.414 1.414L6 12zm0 0 3.707 3.707-1.414 1.414H4v3h3l1.06-1.06L12 12l1.06-1.06L17 11V8a2 2 0 10-4 0v3l-1.06 1.06L4 11h3z" />
          </svg>
        </button>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask JARVIS anything..."
          className="flex-1 min-h-[44px] px-3 py-2 rounded-xl focus:ring-2 focus:ring-cyan-300 resize-none bg-black/50 text-cyan-100 border border-white/6"
          rows={1}
        />

        <div className="flex items-center gap-2">
          {isProcessing && (
            <div className="text-xs text-amber-300 mr-2">Processing</div>
          )}
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className={`px-4 py-2 bg-cyan-400 text-black rounded-xl hover:bg-cyan-300 disabled:opacity-50 transition-colors ${
              !input.trim() || isLoading ? 'cursor-not-allowed' : 'cursor-pointer'
            }`}
          >
            {isLoading ? 'Thinking...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
