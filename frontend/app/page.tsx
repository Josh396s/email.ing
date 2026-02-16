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
    <div className="flex h-screen bg-white text-slate-900 font-sans">
      {/* Sidebar */}
      <aside className="w-72 border-r border-slate-100 p-8 flex flex-col bg-slate-50/50">
        <div className="mb-12">
          <h1 className="text-3xl font-black text-indigo-600 tracking-tighter">Email.ing</h1>
          <div className="flex items-center mt-2">
            <span className={`h-2 w-2 rounded-full mr-2 ${isSyncing ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'}`}></span>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
              {isSyncing ? 'AI Analyzing...' : 'System Ready'}
            </p>
          </div>
        </div>
        
        <nav className="space-y-1 flex-1">
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

        <button 
          onClick={triggerSync}
          disabled={isSyncing}
          className="mt-auto w-full py-4 bg-slate-900 text-white rounded-2xl font-bold text-sm hover:bg-indigo-600 transition-colors disabled:opacity-50"
        >
          {isSyncing ? 'Processing...' : 'Sync Gmail'}
        </button>
        
        <button 
          onClick={handleLogout}
          className="mt-auto w-full py-3 text-slate-400 hover:text-red-500 font-bold text-xs uppercase tracking-widest transition-colors border-t border-slate-100 pt-6"
        >
          Sign Out
        </button>
      </aside>

      {/* Main Feed */}
      <main className="flex-1 overflow-y-auto bg-white">
        <div className="max-w-4xl mx-auto p-12">
          <header className="mb-12">
            <h2 className="text-4xl font-bold tracking-tight text-slate-900">{filter}</h2>
            <p className="text-slate-400 mt-2 font-medium">Prioritized by Gemini 2.5 Flash</p>
          </header>

          <div className="space-y-10">
            {emails
              .filter(e => filter === 'All' || e.category === filter)
              .map((email: any) => (
                <div key={email.id} className="group relative">
                  <div className="flex items-center gap-4 mb-3">
                    <span className="text-xs font-bold text-indigo-500 tracking-wide uppercase">{email.sender}</span>
                    <div className={`h-[1px] flex-1 bg-slate-100`}></div>
                    <span className={`text-[10px] font-black px-2 py-1 rounded-md ${
                      parseInt(email.urgency) >= 4 ? 'bg-red-50 text-red-600' : 'bg-slate-50 text-slate-400'
                    }`}>
                      LVL {email.urgency}
                    </span>
                  </div>
                  
                  <h3 className="text-2xl font-bold text-slate-800 group-hover:text-indigo-600 transition-colors cursor-pointer leading-tight mb-4">
                    {email.subject}
                  </h3>

                  <div className="bg-slate-50/80 border border-slate-100 p-6 rounded-3xl group-hover:bg-indigo-50/30 transition-colors">
                    <p className="text-slate-600 leading-relaxed font-medium">
                      <span className="text-indigo-600 font-bold mr-2 text-sm uppercase tracking-tighter">Agent Note:</span>
                      {email.summary}
                    </p>
                  </div>
                </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );

  
}