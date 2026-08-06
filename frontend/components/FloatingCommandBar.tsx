'use client';

import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { marked } from 'marked';
import { useJarvis } from '@/context/JarvisContext';

interface ChatMessage {
  id: string;
  content: string;
  isUser: boolean;
  tone?: 'normal' | 'status' | 'error';
}

/**
 * Floating command input + holographic transcript. The single entry point for
 * talking to JARVIS - same backend call shape as before (POST /api/chat/message).
 */
export default function FloatingCommandBar() {
  const {
    backendUrl,
    clientId,
    isListening,
    isSpeaking,
    setListening,
    setProcessing,
    setSpeaking,
    backendOnline,
    wsConnected
  } = useJarvis();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recordingChunksRef = useRef<Blob[]>([]);
  const cancelRecordingRef = useRef(false);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => () => {
    recorderRef.current?.stop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isLoading) return;
    if (!backendOnline) {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).substr(2, 9),
          content: 'Backend is disconnected. Start FastAPI on port 8000, then retry.',
          isUser: false,
          tone: 'error'
        }
      ]);
      return;
    }

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
          isUser: false,
          tone: 'error'
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

  const speakWithBrowser = (text: string) => {
    if (!('speechSynthesis' in window) || !text) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  const playResponseAudio = async (base64Audio?: string, mime = 'audio/wav') => {
    if (!base64Audio) return;
    const binary = atob(base64Audio);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    const audio = new Audio(URL.createObjectURL(new Blob([bytes], { type: mime })));
    setSpeaking(true);
    audio.onended = () => {
      URL.revokeObjectURL(audio.src);
      setSpeaking(false);
    };
    audio.onerror = () => {
      setSpeaking(false);
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).slice(2, 11),
          content: 'Voice playback failed. The response is still available as text.',
          isUser: false,
          tone: 'error'
        }
      ]);
    };
    await audio.play();
  };

  const submitRecording = async (audio: Blob) => {
    setListening(false);
    setIsLoading(true);
    setProcessing(true);
    try {
      const form = new FormData();
      form.append('audio', audio, 'jarvis-recording.webm');
      const response = await fetch(
        `${backendUrl}/api/voice/process-voice?language=en&client_id=${encodeURIComponent(clientId)}`,
        { method: 'POST', body: form }
      );
      if (!response.ok) throw new Error(`Backend returned ${response.status}`);
      const data = await response.json();
      if (data.text) {
        setMessages((prev) => [
          ...prev,
          { id: Math.random().toString(36).slice(2, 11), content: data.text, isUser: true }
        ]);
      }
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).slice(2, 11),
          content: data.response || 'I could not understand that recording.',
          isUser: false
        }
      ]);
      if (data.audio_available) {
        await playResponseAudio(data.audio, data.audio_mime);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: Math.random().toString(36).slice(2, 11),
            content: 'Native voice output is unavailable. Using browser speech fallback.',
            isUser: false,
            tone: 'status'
          }
        ]);
        speakWithBrowser(data.response || '');
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).slice(2, 11),
          content: 'Voice processing failed. Check microphone permission and the JARVIS voice services.',
          isUser: false,
          tone: 'error'
        }
      ]);
    } finally {
      setIsLoading(false);
      setProcessing(false);
    }
  };

  const toggleRecording = async () => {
    if (isLoading) return;
    if (recorderRef.current?.state === 'recording') {
      cancelRecordingRef.current = false;
      recorderRef.current.stop();
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).slice(2, 11),
          content: 'Voice input is not supported by this browser.',
          isUser: false,
          tone: 'error'
        }
      ]);
      return;
    }
    try {
      cancelRecordingRef.current = false;
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      recordingChunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) recordingChunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        recorderRef.current = null;
        if (cancelRecordingRef.current) {
          cancelRecordingRef.current = false;
          recordingChunksRef.current = [];
          setListening(false);
          return;
        }
        void submitRecording(new Blob(recordingChunksRef.current, { type: recorder.mimeType || 'audio/webm' }));
      };
      recorder.start();
      setListening(true);
    } catch {
      setListening(false);
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).slice(2, 11),
          content: 'Microphone access was not granted. Enable microphone permission and try again.',
          isUser: false,
          tone: 'error'
        }
      ]);
    }
  };

  const cancelRecording = () => {
    if (recorderRef.current?.state === 'recording') {
      cancelRecordingRef.current = true;
      recorderRef.current.stop();
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape' && isListening) {
      e.preventDefault();
      cancelRecording();
      return;
    }
    handleKeyDown(e);
  };

  const statusText = isListening
    ? 'Recording - Esc cancels'
    : isLoading
      ? 'Planning response'
      : isSpeaking
        ? 'Speaking'
        : backendOnline
          ? 'Ready for command'
          : 'Backend disconnected';

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
                    className={`inline-block max-w-full text-left text-xs leading-relaxed rounded-lg px-2.5 py-1.5 ${
                      msg.isUser
                        ? 'text-cyan-50 bg-cyan-400/10'
                        : msg.tone === 'error'
                          ? 'text-rose-100 bg-rose-500/10 border border-rose-300/15'
                          : msg.tone === 'status'
                            ? 'text-sky-100 bg-sky-400/10 border border-sky-300/10'
                            : 'text-white/90 bg-white/[0.04]'
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
        <div className="relative rounded-2xl hud-panel p-2.5">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2 px-1">
            <span className={`hud-status-text ${backendOnline ? 'text-cyan-100/80' : 'text-rose-200/90'}`}>
              {statusText}
            </span>
            <span className="hud-micro">
              WS {wsConnected ? 'CONNECTED' : 'RECONNECTING'}
            </span>
          </div>
          <div className="flex items-center gap-2">
          <button
            onClick={() => void toggleRecording()}
            className={`hud-icon-btn ${isListening ? 'hud-icon-btn-active' : ''}`}
            aria-label="Toggle listening"
            title={isListening ? 'Stop recording' : 'Start voice input'}
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
            onKeyDown={handleInputKeyDown}
            placeholder={backendOnline ? 'Ask or command JARVIS...' : 'Waiting for backend on port 8000...'}
            className="flex-1 bg-transparent outline-none text-sm text-white/90 placeholder:text-cyan-200/30 tracking-wide min-w-0"
            aria-label="Command JARVIS"
          />
          {isListening && (
            <button
              onClick={cancelRecording}
              className="hud-icon-btn"
              aria-label="Cancel recording"
              title="Cancel recording"
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            </button>
          )}

          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim() || !backendOnline}
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
      </div>
    </motion.div>
  );
}
