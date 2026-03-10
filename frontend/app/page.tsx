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
  Clock,
  Cpu,
  Sparkles,
  Lock,
  Zap
} from 'lucide-react';
import { EmailRow } from '@/src/components/EmailRow';
import { getPriorityStyles } from '@/src/components/EmailRow';

interface Email {
  id: number;
  sender: string;
  subject: string;
  body_text: string;
  category: string;
  urgency: string;
  summary: string;
  is_processed: boolean;
  inference_time: number;
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

  if (logged_out) return <div className="h-screen flex items-center justify-center text-[#F0EAD6] bg-[#95B8BF]">Loading...</div>;

  if (!token) {
    return (
      <main className="h-screen flex flex-col items-center justify-center bg-[#496B73] text-[#F0EAD6] p-6">
        <div className="max-w-md text-center">
          <h1 className="text-6xl font-black mb-4 tracking-tighter text-[#F0EAD6]">Email.ing</h1>
          <p className="text-[#B4BEBF] text-lg mb-10">
            Your AI-first inbox. Summarized, categorized, and prioritized by modular LLMs.
          </p>
          <button 
            onClick={loginWithGoogle}
            className="w-full py-4 bg-[#F0EAD6] text-[#496B73] rounded-2xl font-bold text-lg hover:bg-[#B4BEBF] transition-all shadow-2xl"
          >
            Connect with Gmail
          </button>
          <p className="mt-6 text-xs text-[#B4BEBF] uppercase tracking-widest font-bold">
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
  const [attachments, setAttachments] = useState<any[]>([]);

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
      // Initiate request to fetch new emails and kick off Celery workers
      await fetch('http://localhost:8000/sync', { 
        method: 'POST',
        credentials: 'include'
      });

      // Poll the database every 2 seconds
      const pollInterval = setInterval(async () => {
        const response = await fetch('http://localhost:8000/emails', {
        credentials: 'include'
      });
        
        if (response.ok) {
          const data = await response.json();
          setEmails(data); // This updates the UI as summaries are generated

          // Keep the reading pane updated if an email is open
          setSelectedEmail((prev) => {
          if (!prev) return null;
            // Find the newly updated version of the currently open email
            const updatedEmail = data.find((e: Email) => e.id === prev.id);
            return updatedEmail || prev; 
          });

          // Check if all emails in the UI have finished processing
          const stillProcessing = data.some((e: Email) => !e.is_processed);
          
          if (!stillProcessing) {
            // Workers are completely done. Stop polling.
            clearInterval(pollInterval);
            setIsSyncing(false);
            checkAuthStatus();
          }
        }
      }, 2000);

    } catch (error) {
      console.error("Sync failed:", error);
      setIsSyncing(false);
    }
  };

  const formatLastSynced = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], {
      month: 'short',
      day: 'numeric',
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
    setAttachments([]);

    try {
      const response = await fetch(`http://localhost:8000/emails/${email.id}/body`, {
        credentials: "include",
        cache: "no-store"
      });
      const data = await response.json();

      console.log("Backend response for body:", data);

      setFullBody(data.body || "No content available.");
      setAttachments(data.attachments || []);
    } catch (error) {
      console.error("Fetch error:", error);
      setFullBody("Failed to load email content.");
    }
  };

  const handleDownloadAttachment = async (emailId: number, attachmentId: number, filename: string) => {
    try {
      const response = await fetch(`http://localhost:8000/emails/${emailId}/attachments/${attachmentId}`, {
        credentials: "include", // Ensures JWT cookie is sent
        cache: "no-store"
      });
      
      if (!response.ok) throw new Error("Download failed");
      
      // Convert the response to a Blob and create a temporary URL
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      // Create a hidden link, click it to download, and clean up
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Error downloading attachment:", error);
      alert("Failed to download attachment.");
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
    /* Main Container */
    <div className="flex h-screen bg-[#ffffff]/10 text-[#F0EAD6] font-sans overflow-hidden">
      
      {/* Left SideBar */}
      <aside className="w-60 border-r border-[#88888]/30 p-8 flex flex-col bg-[#88888] flex-shrink-0">
        
        {/* Title and State Information */}
        <div className="mb-12">
          <h1 className="text-4xl font-black text-[#88888] tracking-tighter">Email.ing</h1>
          <div className="flex items-center mt-3">
            <span className={`h-2 w-2 rounded-full mr-2 ${isSyncing ? 'bg-[#F0EAD6] animate-ping' : 'bg-[#5E848C]'}`}></span>
            <p className="text-[13px] font-bold text-[#F0EAD6]/80 uppercase tracking-widest">
              {isSyncing ? 'AI Analyzing...' : 'Up to date'}
            </p>
          </div>
          {!isSyncing && (
            <p className="text-[12px] text-[#F0EAD6]/75 font-medium ml-1.5 mt-0.5">
              Last synced: {formatLastSynced(lastSynced)}
            </p>
          )}
        </div>
        
        {/* Navigation Tabs*/}
        <nav className="space-y-1 flex-1 overflow-y-auto">
          {categories.map(cat => (
            <button 
              key={cat}
              onClick={() => setFilter(cat)}
              className={`w-full text-left px-4 py-3 rounded-xl font-semibold text-med transition-all ${
                filter === cat ? 'bg-[#F0EAD6] shadow-sm text-[#496B73] border border-[#F0EAD6]/50' : 'text-[#F0EAD6]/80 hover:bg-[#F0EAD6]/10'
              }`}
            >
              {cat}
            </button>
          ))}
        </nav>

        {/* Sync and Logout Buttons */}
        <div className="mt-auto space-y-4 pt-6 border-t border-[#7C9EA6]/30">
          <button 
            onClick={triggerSync}
            disabled={isSyncing}
            className={`w-full py-4 flex items-center justify-center gap-2 rounded-2xl font-bold text-sm transition-all ${
              isSyncing 
              ? 'bg-[#B4BEBF]/30 text-[#F0EAD6]/50 cursor-not-allowed' 
              : 'bg-[#496B73] text-[#F0EAD6] hover:bg-[#5E848C]'
            }`}
          >
            <RefreshCw size={16} className={isSyncing ? 'animate-spin' : ''} />
            {isSyncing ? 'AI Analyzing...' : 'Sync Gmail'}
          </button>
          
          <button 
            onClick={handleLogout}
            className="w-full py-3 text-[#F0EAD6]/70 hover:text-[#F0EAD6] font-bold text-xs uppercase tracking-widest transition-colors"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* Middle Pane */}
      <section className="w-1/3 border-r border-[#7C9EA6]/30 flex flex-col bg-[#5E848C]/50 flex-shrink-0 overflow-hidden">
        <div className="p-6 border-b border-[#7C9EA6]/30 flex justify-between items-center">
          <h2 className="text-xl font-bold text-[#F0EAD6]">{filter} Messages</h2>
          <span className="text-[15px] font-bold bg-[#95b8BF]/70 px-2 py-1 rounded text-[#F0EAD6]">
            {emails.filter(e => filter === 'All' || e.category?.toLowerCase() === filter.toLowerCase()).length} Total
          </span>
        </div>
        
        {/* Email List */}
        <div className="flex-1 overflow-y-auto text-[#99999]/80">
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

      {/* Reading Pane */}
      <main className="flex-1 overflow-y-auto bg-[#95B8BF]/65">
        {selectedEmail ? (
          <div className="max-w-5xl mx-auto p-12">
            <header className="mb-4">
              <div className="flex items-center gap-5 mb-5">
                <span className="px-3 py-1 bg-[#496B73]/100 text-[#F0EAD6] text-[12px] font-bold rounded-full uppercase border border-[#7C9EA6]">
                  {selectedEmail.category}
                </span>
                <span className={`text-[12px] font-black px-1.5 py-0.5 rounded border uppercase tracking-wider ${getPriorityStyles(selectedEmail.urgency)}`}>
                  LVL {selectedEmail.urgency}
                </span>
                <span className="text-[#F0EAD6]/90 text-[16px] font-semilight">{selectedEmail.sender}</span>
                {selectedEmail.inference_time && (
                  <span className="px-2 py-1 bg-[#496B73]/80 text-[#F0EAD6] text-[12px] font-mono font-bold rounded flex items-center gap-1 shadow-sm">
                    <Zap size={12} /> Inference: {(selectedEmail.inference_time/1000).toFixed(2)}s
                  </span>
                )}
            
              </div>
              <h1 className="text-[35px] font-extrabold text-[#F0EAD6] tracking-tight leading-tight">
                {selectedEmail.subject}
              </h1>

              {/* Attachment UI */}
              {attachments.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-4">
                  {attachments.map((att) => (
                    <button 
                      key={att.id} 
                      onClick={() => handleDownloadAttachment(selectedEmail.id, att.id, att.filename)}
                      className="px-3 py-1.5 bg-[#496B73]/60 hover:bg-[#496B73] border border-[#7C9EA6]/50 rounded-lg text-xs font-semibold text-[#F0EAD6] flex items-center gap-2 shadow-sm transition-colors cursor-pointer group"
                    >
                      {att.filename}
                      <span className="text-[#B4BEBF] font-normal text-[10px]">
                        {(att.size / 1024).toFixed(1)} KB
                      </span>
                      <span className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity text-[#F0EAD6]">
                        ↓
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </header>

            <div className="bg-[#496B73] text-[#F0EAD6] p-8 rounded-[2rem] mb-12 shadow-xl shadow-[#496B73]/30">
              <h4 className="text-[#95B8BF] text-[10px] font-black uppercase tracking-widest mb-4">Agent Briefing</h4>
              <p className="text-lg font-medium leading-relaxed italic">
                "{selectedEmail.summary}"
              </p>
            </div>

            <article className="email_content">
              <div className="border border-[#7C9EA6]/50 rounded-3xl overflow-hidden bg-white shadow-inner min-h-[600px]">
                {/* The iframe background remains white so standard HTML emails still look correct */}
                <iframe
                  key={selectedEmail.id}
                  title="Email Content"
                  srcDoc={fullBody} 
                  className="w-full h-[700px] border-none bg-white text-black"
                  sandbox="allow-same-origin allow-popups allow-popups-to-escape-sandbox"
                />
              </div>
            </article>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-[#F0EAD6]/60">
            <p className="text-sm font-black uppercase tracking-[0.2em]">Select a message to analyze</p>
          </div>
        )}
      </main>
    </div>
  );
}