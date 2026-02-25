"use client";
import { useEffect, useState } from 'react';

export default function Home() {
  // Variables that maintains user Token after login
  const [token, setToken] = useState<string | null>(null);
  const [logged_out, setLogged_Out] = useState(true);

  // Import user's key if available upon start
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Attempt to authenticate user
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


  // Function to send user to FastAPI auth flow
  const loginWithGoogle = () => {
    window.location.href = "http://localhost:8000/login";
  };

  if (logged_out) return <div className="h-screen flex items-center justify-center">Loading...</div>;

  // Display login page if no token is available
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

  // Display main page if token is available
  return <SmartInbox/>;
}

function SmartInbox() {
  const [emails, setEmails] = useState([]);
  const [filter, setFilter] = useState('All');
  const [isSyncing, setIsSyncing] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<any>(null);
  const [fullBody, setFullBody] = useState<string>("");

  const fetchEmails = async () => {
    setIsSyncing(true);

    try {
      // Get user's emails
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
      setTimeout(fetchEmails, 3000);
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSelectEmail = async (email: any) => {
    setSelectedEmail(email);
    setFullBody("Decrypting message..."); // Loading state

    try {
      const response = await fetch(`http://localhost:8000/emails/${email.id}/body`, {
        credentials: "include",
      });
      const data = await response.json();
      setFullBody(data.body);
    } catch (error) {
      setFullBody("Failed to load email content.");
    }
  };

  const handleLogout = async () => {
    try {
      
      await fetch("http://localhost:8000/logout", {
        method: "GET",
        credentials: "include", // Required to tell the backend WHICH cookie to delete
      });

      // 2. Refresh the page
      // This resets all React state and triggers the Home() component 
      // to re-run its checkAuth(), which will now fail and show the login page.
      window.location.reload();
    } catch (error) {
      console.error("Logout failed", error);
    }
  };

  useEffect(() => { fetchEmails(); }, []);

  const categories = ['All', 'Work', 'Personal', 'Newsletter', 'Transactional'];

  return (
    <div className="flex h-screen bg-white text-slate-900 font-sans overflow-hidden">
      
      {/* 1. SIDEBAR (Fixed Width) */}
      <aside className="w-72 border-r border-slate-100 p-8 flex flex-col bg-slate-50/50 flex-shrink-0">
        <div className="mb-12">
          <h1 className="text-3xl font-black text-indigo-600 tracking-tighter">Email.ing</h1>
          <div className="flex items-center mt-2">
            <span className={`h-2 w-2 rounded-full mr-2 ${isSyncing ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'}`}></span>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              {isSyncing ? 'AI Analyzing...' : 'System Ready'}
            </p>
          </div>
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
            className="w-full py-4 bg-slate-900 text-white rounded-2xl font-bold text-sm hover:bg-indigo-600 transition-colors disabled:opacity-50"
          >
            {isSyncing ? 'Processing...' : 'Sync Gmail'}
          </button>
          
          <button 
            onClick={handleLogout}
            className="w-full py-3 text-slate-400 hover:text-red-500 font-bold text-xs uppercase tracking-widest transition-colors"
          >
            Sign Out
          </button>
        </div>
      </aside>

      {/* 2. MIDDLE PANE (Email List - 1/3 Width) */}
      <section className="w-1/3 border-r border-slate-100 flex flex-col bg-white flex-shrink-0 overflow-hidden">
        <div className="p-6 border-b border-slate-50">
          <h2 className="text-xl font-bold text-slate-900">{filter} Messages</h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {emails
            .filter(e => filter === 'All' || e.category === filter)
            .map((email: any) => (
              <div 
                key={email.id} 
                onClick={() => handleSelectEmail(email)}
                className={`p-6 border-b border-slate-50 cursor-pointer transition-all ${
                  selectedEmail?.id === email.id ? 'bg-indigo-50/50 border-l-4 border-l-indigo-600' : 'hover:bg-slate-50'
                }`}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[10px] font-bold text-indigo-500 uppercase truncate max-w-[120px]">
                    {email.sender}
                  </span>
                  <span className={`text-[10px] font-black px-1.5 py-0.5 rounded ${
                    parseInt(email.urgency) >= 4 ? 'bg-red-50 text-red-600' : 'bg-slate-100 text-slate-400'
                  }`}>
                    LVL {email.urgency}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-800 truncate mb-1">{email.subject}</h3>
                <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">{email.summary}</p>
              </div>
            ))}
        </div>
      </section>

      {/* 3. READING PANE (Detail View - Remaining Space) */}
      <main className="flex-1 overflow-y-auto bg-white">
        {selectedEmail ? (
          <div className="max-w-3xl mx-auto p-12">
            <header className="mb-8">
              <div className="flex items-center gap-3 mb-6">
                <span className="px-3 py-1 bg-indigo-100 text-indigo-700 text-[10px] font-bold rounded-full uppercase">
                  {selectedEmail.category}
                </span>
                <span className="text-slate-400 text-xs font-medium">{selectedEmail.sender}</span>
              </div>
              <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
                {selectedEmail.subject}
              </h1>
            </header>

            {/* AI Briefing Card */}
            <div className="bg-slate-900 text-white p-8 rounded-[2rem] mb-12 shadow-2xl shadow-indigo-100">
              <h4 className="text-indigo-400 text-[10px] font-black uppercase tracking-widest mb-4">Agent Briefing</h4>
              <p className="text-lg font-medium leading-relaxed italic">
                "{selectedEmail.summary}"
              </p>
            </div>

            {/* Decrypted Content */}
            <article className="prose prose-slate max-w-none">
              <div className="border border-slate-100 rounded-3xl overflow-hidden bg-white shadow-inner min-h-[500px]">
                <iframe
                  title="Email Content"
                  srcDoc={fullBody} // fullBody now contains the HTML
                  className="w-full h-[600px] border-none"
                  sandbox="allow-popups allow-popups-to-escape-sandbox" // Prevents the email from running JS
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