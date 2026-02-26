"use client";
import { useEffect, useState } from 'react';
import { 
  RefreshCw, 
  Briefcase, 
  User, 
  Newspaper, 
  CreditCard, 
  AlertTriangle, 
  Mail,
  Clock
} from 'lucide-react';
import { EmailRow } from '@/src/components/EmailRow';
import { getPriorityStyles } from '@/src/components/EmailRow';

// Define the Email interface for better type safety
interface Email {
  id: number;
  sender: string;
  subject: string;
  body_text: string;
  category: string;
  urgency: string;
  summary: string;
  is_processed: boolean;
}

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [logged_out, setLogged_Out] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch("http://localhost:8000/auth/status", {
          method: "GET",
          credentials: "include", 
        });

        if (response.ok) {
          setToken("authenticated"); 
        } else {
          setToken(null);
        }
      } catch (error) {
        console.error("Auth check failed", error);
        setToken(null);
      } finally {
        setLogged_Out(false);
      }
    };
    checkAuth();
  }, []);

  const loginWithGoogle = () => {
    window.location.href = "http://localhost:8000/login";
  };

  if (logged_out) return <div className="h-screen flex items-center justify-center">Loading...</div>;

  if (!token) {
    return (
      <main className="h-screen flex flex-col items-center justify-center bg-slate-950 text-white p-6">
        <div className="max-w-md text-center">
          <h1 className="text-6xl font-black mb-4 tracking-tighter text-indigo-500">Email.ing</h1>
          <p className="text-slate-400 text-lg mb-10">
            Your AI-first inbox. Summarized, categorized, and prioritized by Gemini 2.5.
          </p>
          <button 
            onClick={loginWithGoogle}
            className="w-full py-4 bg-white text-black rounded-2xl font-bold text-lg hover:bg-indigo-500 hover:text-white transition-all shadow-2xl"
          >
            Connect with Gmail
          </button>
          <p className="mt-6 text-xs text-slate-500 uppercase tracking-widest font-bold">
            Securely encrypted via Fernet-AES
          </p>
        </div>
      </main>
    );
  }

  return <SmartInbox/>;
}

function SmartInbox() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [filter, setFilter] = useState('All');
  const [isSyncing, setIsSyncing] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [fullBody, setFullBody] = useState<string>("");
  const [lastSynced, setLastSynced] = useState<string | null>(null);

  const fetchEmails = async () => {
    setIsSyncing(true);
    try {
      const response = await fetch('http://localhost:8000/emails', {
        method: 'GET',
        credentials: 'include', 
      });

      if (response.ok) {
        const data = await response.json();
        setEmails(data);
      } else if (response.status === 401) {
        window.location.reload(); 
      }
    } catch (error) {
      console.error("Fetch failed:", error);
    } finally {
      setIsSyncing(false);
    }
  };

  const triggerSync = async () => {
    setIsSyncing(true);
    try {
      await fetch('http://localhost:8000/sync', { 
        method: 'POST',
        credentials: 'include'
      });
      setTimeout(() => {
        fetchEmails();
        checkAuthStatus(); 
      }, 3000);
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setIsSyncing(false);
    }
  };

  const formatLastSynced = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };

  const checkAuthStatus = async () => {
    try {
      const response = await fetch("http://localhost:8000/auth/status", {
        method: "GET",
        credentials: "include", 
      });
      if (response.ok) {
        const data = await response.json();
        setLastSynced(data.last_synced);
      }
    } catch (error) {
      console.error("Failed to check status", error);
    }
  };

  useEffect(() => { 
    fetchEmails(); 
    checkAuthStatus(); 
  }, []);

  const handleSelectEmail = async (email: any) => {
    setSelectedEmail(email);
    setFullBody("Decrypting message...");

    try {
      const response = await fetch(`http://localhost:8000/emails/${email.id}/body`, {
        credentials: "include",
      });
      const data = await response.json();
      setFullBody(data.body || "No content available.");
    } catch (error) {
      setFullBody("Failed to load email content.");
    }
  };

  const handleLogout = async () => {
    try {
      await fetch("http://localhost:8000/logout", {
        method: "GET",
        credentials: "include",
      });
      window.location.reload();
    } catch (error) {
      console.error("Logout failed", error);
    }
  };

  const categories = ['All', 'Work', 'Personal', 'Newsletter', 'Transactional'];

  return (
    <div className="flex h-screen bg-white text-slate-900 font-sans overflow-hidden">
      
      {/* SIDEBAR */}
      <aside className="w-72 border-r border-slate-100 p-8 flex flex-col bg-slate-50/50 flex-shrink-0">
        <div className="mb-12">
          <h1 className="text-3xl font-black text-indigo-600 tracking-tighter">Email.ing</h1>
          <div className="flex items-center mt-2">
            <span className={`h-2 w-2 rounded-full mr-2 ${isSyncing ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'}`}></span>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              {isSyncing ? 'AI Analyzing...' : 'System Ready'}
            </p>
          </div>
          {!isSyncing && (
            <p className="text-[9px] text-slate-400 font-medium ml-4 mt-1">
              Last synced: {formatLastSynced(lastSynced)}
            </p>
          )}
        </div>
        
        <nav className="space-y-1 flex-1 overflow-y-auto">
          {categories.map(cat => (
            <button 
              key={cat}
              onClick={() => setFilter(cat)}
              className={`w-full text-left px-4 py-3 rounded-xl font-semibold text-sm transition-all ${
                filter === cat ? 'bg-white shadow-sm text-indigo-600 border border-slate-100' : 'text-slate-500 hover:bg-white/50'
              }`}
            >
              {cat}
            </button>
          ))}
        </nav>

        <div className="mt-auto space-y-4 pt-6 border-t border-slate-100">
          <button 
            onClick={triggerSync}
            disabled={isSyncing}
            className={`w-full py-4 flex items-center justify-center gap-2 rounded-2xl font-bold text-sm transition-all ${
              isSyncing 
              ? 'bg-indigo-100 text-indigo-400 cursor-not-allowed' 
              : 'bg-slate-900 text-white hover:bg-indigo-600'
            }`}
          >
            <RefreshCw size={16} className={isSyncing ? 'animate-spin' : ''} />
            {isSyncing ? 'AI Analyzing...' : 'Sync Gmail'}
          </button>
          
          <button 
            onClick={handleLogout}
            className="w-full py-3 text-slate-400 hover:text-red-500 font-bold text-xs uppercase tracking-widest transition-colors"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* MIDDLE PANE */}
      <section className="w-1/3 border-r border-slate-100 flex flex-col bg-white flex-shrink-0 overflow-hidden">
        <div className="p-6 border-b border-slate-50 flex justify-between items-center">
          <h2 className="text-xl font-bold text-slate-900">{filter} Messages</h2>
          <span className="text-[10px] font-bold bg-slate-100 px-2 py-1 rounded text-slate-500">
            {emails.filter(e => filter === 'All' || e.category?.toLowerCase() === filter.toLowerCase()).length} Total
          </span>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {emails
            .filter(e => filter === 'All' || e.category?.toLowerCase() === filter.toLowerCase())
            .map((email: Email) => (
              <EmailRow 
                key={email.id}
                email={email}
                isSelected={selectedEmail?.id === email.id} 
                onSelect={handleSelectEmail}
              />
            ))}
        </div>
      </section>

      {/* READING PANE */}
      <main className="flex-1 overflow-y-auto bg-white">
        {selectedEmail ? (
          <div className="max-w-3xl mx-auto p-12">
            <header className="mb-8">
              <div className="flex items-center gap-3 mb-6">
                <span className="px-3 py-1 bg-indigo-100 text-indigo-700 text-[10px] font-bold rounded-full uppercase">
                  {selectedEmail.category}
                </span>
                <span className={`text-[9px] font-black px-1.5 py-0.5 rounded border uppercase tracking-wider ${getPriorityStyles(selectedEmail.urgency)}`}>
                  LVL {selectedEmail.urgency}
                </span>
                <span className="text-slate-400 text-xs font-medium">{selectedEmail.sender}</span>
              </div>
              <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
                {selectedEmail.subject}
              </h1>
            </header>

            <div className="bg-slate-900 text-white p-8 rounded-[2rem] mb-12 shadow-2xl shadow-indigo-100">
              <h4 className="text-indigo-400 text-[10px] font-black uppercase tracking-widest mb-4">Agent Briefing</h4>
              <p className="text-lg font-medium leading-relaxed italic">
                "{selectedEmail.summary}"
              </p>
            </div>

            <article className="prose prose-slate max-w-none mb-10">
              <div className="border border-slate-100 rounded-3xl overflow-hidden bg-white shadow-inner min-h-[500px]">
                <iframe
                  title="Email Content"
                  srcDoc={fullBody} 
                  className="w-full h-[600px] border-none"
                  sandbox="allow-popups allow-popups-to-escape-sandbox" 
                />
              </div>
            </article>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-200">
            <p className="text-sm font-black uppercase tracking-[0.2em]">Select a message to analyze</p>
          </div>
        )}
      </main>
    </div>
  );
}