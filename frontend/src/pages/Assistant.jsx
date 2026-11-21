import React, { useState, useEffect, useRef } from 'react';
import { aiAPI, subjectsAPI, examsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  Bot,
  Send,
  Sparkles,
  Trash2,
  User,
  GraduationCap,
  BookOpen,
  ArrowRight,
  HelpCircle,
  Cpu,
  Info,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

const SUGGESTIONS = [
  "Which subjects and topics should I prioritize based on my progress?",
  "Explain the Pomodoro technique with an example.",
  "What is the difference between active recall and passive learning?",
  "Explain binary search with a simple C++ and Python example.",
  "Suggest a study routine based on my available time.",
  "How many hours have I studied this week?",
  "Give me a practical strategy for improving concentration."
];

export default function Assistant() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [subjectsCount, setSubjectsCount] = useState(0);
  const [examsCount, setExamsCount] = useState(0);
  const [aiStatus, setAiStatus] = useState({ mode: 'fallback', is_available: false, model: 'gpt-4o-mini' });
  const [showStatusTip, setShowStatusTip] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    // 1. Check AI engine status (Live OpenAI vs. Offline Academic Engine)
    aiAPI.getStatus().then((res) => {
      setAiStatus(res.data);
      if (res.data.mode === 'fallback') {
        setShowStatusTip(true);
      }
    }).catch(() => {
      setAiStatus({ mode: 'fallback', is_available: false, model: 'gpt-4o-mini' });
    });

    // 2. Load conversations
    aiAPI.getConversations().then((res) => {
      if (res.data.length > 0) {
        const latest = res.data[0];
        setConversationId(latest.id);
        setMessages(latest.messages || []);
      } else {
        // Initial welcome message
        setMessages([
          {
            id: 'welcome',
            sender: 'assistant',
            content: `Hello ${user?.full_name?.split(' ')[0] || 'there'}! I am your AI Study Assistant. I have verified access to your enrolled subjects, pending topics, upcoming examinations, and study hours to deliver grounded academic guidance.\n\nAsk me about concept explanations (with C++ or Python code), exam revision strategies, personalized routines, or how to master your hardest subjects!`
          }
        ]);
      }
    }).catch(console.error);

    subjectsAPI.getAll().then(res => setSubjectsCount(res.data.length)).catch(console.error);
    examsAPI.getAll().then(res => setExamsCount(res.data.length)).catch(console.error);
  }, [user]);

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      content: text
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await aiAPI.chat({
        content: text,
        conversation_id: conversationId
      });

      setConversationId(res.data.conversation_id);
      setMessages((prev) => [...prev, res.data.assistant_message]);
      if (res.data.mode) {
        setAiStatus(prev => ({ ...prev, mode: res.data.mode }));
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          content: 'I encountered a brief connection issue. Please verify your message and try again.'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearChat = async () => {
    if (conversationId) {
      try {
        await aiAPI.clearConversation(conversationId);
      } catch (err) {
        console.error(err);
      }
    }
    setConversationId(null);
    setMessages([
      {
        id: 'welcome',
        sender: 'assistant',
        content: `Chat history cleared. What topic or exam strategy would you like to explore next?`
      }
    ]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] max-w-4xl mx-auto rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between shrink-0 bg-white dark:bg-slate-900">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">
                AI Study Assistant
              </h3>
              {aiStatus.mode === 'openai' ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Live AI ({aiStatus.model})
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/40">
                  <Cpu className="w-3 h-3 text-indigo-500" />
                  Academic Engine
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Verified Context: {subjectsCount} Subject(s) • {examsCount} Upcoming Exam(s)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleClearChat}
            title="Clear Chat History"
            className="p-2 rounded-xl text-slate-400 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Engine Status Banner (Dismissible) */}
      {showStatusTip && (
        <div className="bg-gradient-to-r from-indigo-50/70 via-brand-50/50 to-indigo-50/70 dark:from-indigo-950/30 dark:via-slate-900 dark:to-indigo-950/30 px-6 py-2 border-b border-indigo-100 dark:border-indigo-900/30 flex items-center justify-between text-xs text-indigo-800 dark:text-indigo-300">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-brand-600 shrink-0" />
            <span>
              <strong>Engine Mode:</strong> Built-in Academic Knowledge Engine is active. To enable live GPT-4o-mini generation, set a valid <code>OPENAI_API_KEY</code> in <code>backend/.env</code>.
            </span>
          </div>
          <button
            onClick={() => setShowStatusTip(false)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 ml-4 font-bold"
          >
            ×
          </button>
        </div>
      )}

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
        {messages.map((m) => {
          const isUser = m.sender === 'user';
          return (
            <div
              key={m.id}
              className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 ${
                  isUser
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'bg-indigo-100 dark:bg-indigo-950/60 text-brand-600 dark:text-brand-300'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  isUser
                    ? 'bg-brand-600 text-white rounded-tr-none shadow-md shadow-brand-500/15'
                    : 'bg-slate-100 dark:bg-slate-800/60 text-slate-800 dark:text-slate-200 rounded-tl-none whitespace-pre-wrap'
                }`}
              >
                {m.content}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-xl bg-indigo-100 dark:bg-indigo-950/60 text-brand-600 flex items-center justify-center text-xs shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-slate-100 dark:bg-slate-800/60 rounded-2xl rounded-tl-none px-4 py-3 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-brand-500 animate-bounce" />
              <span className="w-2 h-2 rounded-full bg-brand-500 animate-bounce [animation-delay:0.2s]" />
              <span className="w-2 h-2 rounded-full bg-brand-500 animate-bounce [animation-delay:0.4s]" />
              <span className="text-xs text-slate-400 ml-2">Consulting academic context...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts Pill Carousel */}
      {messages.length <= 4 && (
        <div className="px-4 py-2.5 border-t border-slate-100 dark:border-slate-800/60 flex items-center gap-2 overflow-x-auto shrink-0 bg-slate-50/50 dark:bg-slate-900/50">
          <span className="text-[11px] font-semibold text-slate-400 shrink-0">Try asking:</span>
          {SUGGESTIONS.map((s, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(s)}
              className="text-[11px] px-3 py-1 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-brand-50 dark:hover:bg-brand-950/40 hover:text-brand-600 dark:hover:text-brand-300 transition-colors shrink-0 text-slate-600 dark:text-slate-300 shadow-sm"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input Bar */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800 shrink-0 bg-white dark:bg-slate-900">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your study schedule, exam strategy, or concept explanation..."
            disabled={loading}
            className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40 disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-500/20 disabled:opacity-50 transition-all shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
