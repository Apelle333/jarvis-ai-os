'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { marked } from 'marked';
import { useJarvis } from '@/context/JarvisContext';

interface ChatMessage {
  id: string;
  content: string;
  isUser: boolean;
}

/**
 * Floating command input + holographic transcript. The single entry point for
 * talking to JARVIS - same backend call shape as before (POST /api/chat/message).
 */
export default function FloatingCommandBar() {
  const { backendUrl, isListening, setListening, setProcessing } = useJarvis();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const transcriptRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMessage: ChatMessage = {
      id: Math.random().toString(36).substr(2, 9),
      content: text,
      isUser: true
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setProcessing(true);

    try {
      const response = await fetch(`${backendUrl}/api/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, modality: 'text' })
      });
      if (!response.ok) throw new Error(`Backend returned ${response.status}`);
      const data = await response.json();
      const botContent = data.response || 'No response received.';
      setMessages((prev) => [
        ...prev,
        { id: Math.random().toString(36).substr(2, 9), content: botContent, isUser: false }
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).substr(2, 9),
          content: `Connection lost while reaching the JARVIS core. Retry when the link is stable.`,
          isUser: false
        }
      ]);
    } finally {
      setIsLoading(false);
      setProcessing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, ease: 'easeOut', delay: 0.2 }}
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 w-[min(760px,92vw)] pointer-events-none"
    >
      {/* Transcript */}
      <AnimatePresence>
        {(messages.length > 0 || isLoading) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.25 }}
            className="pointer-events-auto mb-3"
          >
            <div className="hud-panel p-3 max-h-52 overflow-y-auto hud-scroll" ref={transcriptRef}>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`mb-2 last:mb-0 ${msg.isUser ? 'text-right' : 'text-left'}`}
                >
                  <p className="text-[9px] tracking-[0.3em] text-cyan-300/50 mb-0.5">
                    {msg.isUser ? 'YOU' : 'JARVIS'}
                  </p>
                  <div
                    className={`inline-block max-w-full text-left text-xs leading-relaxed ${
                      msg.isUser
                        ? 'text-cyan-100/90'
                        : 'text-white/85'
                    } ${msg.isUser ? '' : 'prose-sm'}`}
                    dangerouslySetInnerHTML={{
                      __html: marked.parse(msg.content) as string
                    }}
                  />
                </div>
              ))}
              {isLoading && (
                <div className="flex items-center gap-2 text-[10px] tracking-[0.3em] text-cyan-300/70">
                  <span className="flex gap-1">
                    <span className="w-1 h-1 rounded-full bg-cyan-300 animate-pulse" />
                    <span className="w-1 h-1 rounded-full bg-cyan-300 animate-pulse [animation-delay:150ms]" />
                    <span className="w-1 h-1 rounded-full bg-cyan-300 animate-pulse [animation-delay:300ms]" />
                  </span>
                  SYNTHESIZING
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Command bar */}
      <div className="pointer-events-auto relative">
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-cyan-500/30 via-sky-400/20 to-cyan-500/30 blur-md opacity-60" />
        <div className="relative flex items-center gap-2 px-3 py-2.5 rounded-2xl hud-panel">
          <button
            onClick={() => setListening(!isListening)}
            className={`hud-icon-btn ${isListening ? 'hud-icon-btn-active' : ''}`}
            aria-label="Toggle listening"
            title="Audio link"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
            </svg>
          </button>

          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Command JARVIS..."
            className="flex-1 bg-transparent outline-none text-sm text-white/90 placeholder:text-cyan-200/30 tracking-wide min-w-0"
          />

          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className={`hud-send-btn ${isLoading ? 'hud-send-active' : ''}`}
            aria-label="Send"
          >
            {isLoading ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2a10 10 0 1 0 10 10" />
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2 11 13" />
                <path d="M22 2 15 22l-4-9-9-4z" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </motion.div>
  );
}
