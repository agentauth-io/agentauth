import { useState, useEffect, useRef } from "react";
import { motion } from "motion/react";
import { Key, Copy, Trash2, Plus, LogOut, Check, Eye, EyeOff, Mail, Lock, Loader2, ExternalLink, User, Building, Github, Settings, Clock, Sparkles } from "lucide-react";
import { supabase, signIn, signUp, signOut, signInWithGoogle, signInWithGithub, getLocalApiKeys, saveLocalApiKeys, checkBetaAccess, setBetaAccessLocal, clearBetaAccessLocal, type ApiKey } from "../../lib/supabase";

interface DeveloperPortalProps {
  onClose?: () => void;
}

export function DeveloperPortal({ onClose }: DeveloperPortalProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const [hasBetaAccess, setHasBetaAccess] = useState<boolean | null>(null);
  const [view, setView] = useState<"login" | "signup" | "verify" | "settings">("login");
  const mountedRef = useRef(true);
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("Default");
  const [newKeyEnv, setNewKeyEnv] = useState<"test" | "live">("test");
  const [newKeyValue, setNewKeyValue] = useState("");

  useEffect(() => {
    mountedRef.current = true;
    
    const initAuth = async () => {
      try {
        const hash = window.location.hash;
        if (hash.includes("access_token")) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        const { data: { session } } = await supabase.auth.getSession();
        if (!mountedRef.current) return;
        
        if (session?.user) {
          setUser(session.user);
          setApiKeys(getLocalApiKeys());
          
          // Check beta access
          const hasAccess = await checkBetaAccess(session.user.email || "");
          if (mountedRef.current) {
            setHasBetaAccess(hasAccess);
            setBetaAccessLocal(hasAccess);
          }
          
          if (hash.includes("access_token")) {
            window.history.replaceState(null, "", "/#portal");
          }
        }
      } catch (err) {
        console.error('Auth init error:', err);
      }
      if (mountedRef.current) setIsLoading(false);
    };
    
    initAuth();
    
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (!mountedRef.current) return;
      
      if (session?.user) {
        setUser(session.user);
        setApiKeys(getLocalApiKeys());
        const hasAccess = await checkBetaAccess(session.user.email || "");
        if (mountedRef.current) {
          setHasBetaAccess(hasAccess);
          setBetaAccessLocal(hasAccess);
        }
        setIsLoading(false);
      } else if (event === 'SIGNED_OUT') {
        setUser(null);
        setHasBetaAccess(null);
        setApiKeys([]);
        clearBetaAccessLocal();
      }
    });
    
    return () => {
      mountedRef.current = false;
      subscription.unsubscribe();
    };
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    const { error } = await signIn(email, password);
    if (error) setError(error.message);
    setIsLoading(false);
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password.length < 8) { setError("Password must be at least 8 characters"); return; }
    setIsLoading(true);
    const { error } = await signUp(email, password, { name, company });
    if (error) { setError(error.message); } else { setView("verify"); }
    setIsLoading(false);
  };

  const handleGoogleLogin = async () => { setError(""); const { error } = await signInWithGoogle(); if (error) setError(error.message); };
  const handleGithubLogin = async () => { setError(""); const { error } = await signInWithGithub(); if (error) setError(error.message); };
  const handleLogout = async () => { await signOut(); setUser(null); setHasBetaAccess(null); setApiKeys([]); setView("login"); clearBetaAccessLocal(); };

  const handleCreateKey = async () => {
    const randomPart = Array.from(crypto.getRandomValues(new Uint8Array(24))).map(b => b.toString(16).padStart(2, '0')).join('');
    const fullKey = `aa_${newKeyEnv}_${randomPart}`;
    setNewKeyValue(fullKey);
    const newKey: ApiKey = { id: crypto.randomUUID(), developer_id: user?.id || 'local', key_prefix: fullKey.substring(0, 20) + "...", key_hash: '', name: newKeyName, environment: newKeyEnv, created_at: new Date().toISOString() };
    const updatedKeys = [newKey, ...apiKeys];
    setApiKeys(updatedKeys);
    saveLocalApiKeys(updatedKeys);
  };

  const handleRevokeKey = (keyId: string) => { const updatedKeys = apiKeys.filter(k => k.id !== keyId); setApiKeys(updatedKeys); saveLocalApiKeys(updatedKeys); };
  const copyToClipboard = (text: string) => { navigator.clipboard.writeText(text); setSuccess("Copied!"); setTimeout(() => setSuccess(""), 2000); };

  if (isLoading) {
    return (
      <section className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
        <div className="text-center"><Loader2 className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-4" /><p className="text-gray-400">Loading...</p></div>
      </section>
    );
  }

  // Waitlist Status Page (for users without beta access)
  if (user && hasBetaAccess === false) {
    return (
      <section className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
        <motion.div className="w-full max-w-md text-center" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 rounded-3xl p-8 backdrop-blur-xl">
            <div className="w-20 h-20 bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/30 rounded-full flex items-center justify-center mx-auto mb-6">
              <Clock className="w-10 h-10 text-amber-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">You're on the Waitlist!</h1>
            <p className="text-gray-400 mb-6">Thanks for signing up, <span className="text-purple-400">{user.email}</span></p>
            
            <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 mb-6">
              <p className="text-amber-300 text-sm">We're currently in private beta. Join our waitlist on the homepage to get early access!</p>
            </div>

            <div className="space-y-3">
              <a href="/" className="block w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-xl font-medium text-center">Join the Waitlist</a>
              <button onClick={handleLogout} className="w-full bg-white/5 hover:bg-white/10 text-gray-400 py-3 rounded-xl flex items-center justify-center gap-2"><LogOut className="w-4 h-4" /> Sign Out</button>
            </div>
          </div>
          {onClose && <button onClick={onClose} className="mt-6 text-gray-400 hover:text-white text-sm">← Back</button>}
        </motion.div>
      </section>
    );
  }

  if (view === "verify") {
    return (
      <section className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
        <motion.div className="w-full max-w-md text-center" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 border border-purple-500/20 rounded-3xl p-8"><div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-6"><Mail className="w-8 h-8 text-white" /></div><h2 className="text-2xl font-bold text-white mb-2">Check your email</h2><p className="text-gray-400 mb-6">We've sent a verification link to <span className="text-purple-400">{email}</span></p><button onClick={() => setView("login")} className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-xl">Back to Sign In</button></div>
        </motion.div>
      </section>
    );
  }

  if (view === "settings" && user) {
    return (
      <section className="min-h-screen px-6 py-12 bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center justify-between mb-8"><h1 className="text-3xl font-bold text-white">Settings</h1><button onClick={() => setView("login")} className="text-gray-400 hover:text-white">← Dashboard</button></div>
          <div className="bg-white/5 border border-white/10 rounded-2xl p-6"><h2 className="text-xl font-semibold text-white mb-4">Profile</h2><div><label className="block text-sm text-gray-400 mb-2">Email</label><input value={user.email} disabled className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-gray-400" /></div></div>
        </div>
      </section>
    );
  }

  if (!user) {
    return (
      <section className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
        <motion.div className="w-full max-w-md" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500/20 to-blue-500/20 border border-purple-500/30 rounded-full mb-4"><Key className="w-4 h-4 text-purple-400" /><span className="text-purple-300 text-sm font-medium">Developer Portal</span></div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent mb-2">{view === "signup" ? "Create account" : "Welcome back"}</h1>
            <p className="text-gray-400">{view === "signup" ? "Start building with AgentAuth" : "Sign in to manage your API keys"}</p>
          </div>
          <div className="bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 rounded-3xl p-8 backdrop-blur-xl shadow-2xl">
            {error && <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">⚠️ {error}</div>}
            <div className="grid grid-cols-2 gap-3 mb-6">
              <button onClick={handleGoogleLogin} className="flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white py-3 rounded-xl"><svg className="w-5 h-5" viewBox="0 0 24 24"><path fill="#EA4335" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#4285F4" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg><span className="text-sm">Google</span></button>
              <button onClick={handleGithubLogin} className="flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white py-3 rounded-xl"><Github className="w-5 h-5" /><span className="text-sm">GitHub</span></button>
            </div>
            <div className="flex items-center gap-4 mb-6"><div className="flex-1 h-px bg-white/20" /><span className="text-gray-500 text-sm">or</span><div className="flex-1 h-px bg-white/20" /></div>
            <form onSubmit={view === "login" ? handleLogin : handleSignup}>
              <div className="space-y-4">
                {view === "signup" && (<div className="grid grid-cols-2 gap-3"><div><label className="block text-sm text-gray-400 mb-2">Name</label><input type="text" value={name} onChange={e => setName(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white" placeholder="John" required /></div><div><label className="block text-sm text-gray-400 mb-2">Company</label><input type="text" value={company} onChange={e => setCompany(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white" placeholder="Acme" /></div></div>)}
                <div><label className="block text-sm text-gray-400 mb-2">Email</label><input type="email" value={email} onChange={e => setEmail(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white" placeholder="you@example.com" required /></div>
                <div><label className="block text-sm text-gray-400 mb-2">Password</label><div className="relative"><input type={showPassword ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white pr-10" placeholder="••••••••" required /><button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">{showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}</button></div></div>
                <button type="submit" className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3.5 rounded-xl font-semibold">{view === "login" ? "Sign In" : "Create Account"}</button>
              </div>
            </form>
            <p className="mt-6 text-center text-gray-400 text-sm">{view === "login" ? <>No account? <button onClick={() => setView("signup")} className="text-purple-400">Sign up</button></> : <>Have an account? <button onClick={() => setView("login")} className="text-purple-400">Sign in</button></>}</p>
          </div>
          {onClose && <button onClick={onClose} className="mt-6 text-gray-400 hover:text-white text-sm mx-auto block">← Back</button>}
        </motion.div>
      </section>
    );
  }

  // Dashboard (only shown for users with beta access)
  return (
    <section className="min-h-screen px-6 py-12 bg-gradient-to-br from-[#0A0A0F] via-[#12121A] to-[#0A0A0F]">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">Developer Dashboard</h1>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-500/20 border border-purple-500/30 rounded-full text-xs text-purple-300"><Sparkles className="w-3 h-3" /> Beta</span>
            </div>
            <p className="text-gray-400">{user?.email}</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setView("settings")} className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl"><Settings className="w-5 h-5" /></button>
            <button onClick={handleLogout} className="flex items-center gap-2 text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 px-4 py-2 rounded-xl"><LogOut className="w-4 h-4" /> Sign Out</button>
          </div>
        </div>

        {success && <div className="mb-6 p-3 bg-green-500/10 border border-green-500/20 rounded-xl text-green-400 flex items-center gap-2"><Check className="w-4 h-4" /> {success}</div>}

        <motion.div className="bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 rounded-2xl p-6 mb-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center justify-between mb-6"><h2 className="text-xl font-semibold text-white flex items-center gap-2"><Key className="w-5 h-5 text-purple-400" /> API Keys</h2><button onClick={() => setShowNewKeyModal(true)} className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-xl text-sm font-medium"><Plus className="w-4 h-4" /> Create Key</button></div>
          {apiKeys.length === 0 ? (<div className="text-center py-12"><Key className="w-8 h-8 text-gray-500 mx-auto mb-2" /><p className="text-gray-400">No API keys yet</p><p className="text-gray-500 text-sm">Create your first key to start</p></div>) : (<div className="space-y-3">{apiKeys.map(key => (<div key={key.id} className="flex items-center justify-between bg-white/5 border border-white/10 rounded-xl p-4"><div><div className="flex items-center gap-2"><span className="text-white font-mono text-sm">{key.key_prefix}</span><span className={`text-xs px-2 py-0.5 rounded-full ${key.environment === 'live' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{key.environment}</span></div><p className="text-gray-500 text-sm mt-1">{key.name} • {new Date(key.created_at).toLocaleDateString()}</p></div><div className="flex gap-1"><button onClick={() => copyToClipboard(key.key_prefix)} className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg"><Copy className="w-4 h-4" /></button><button onClick={() => handleRevokeKey(key.id)} className="p-2 text-gray-400 hover:text-red-400 rounded-lg"><Trash2 className="w-4 h-4" /></button></div></div>))}</div>)}
        </motion.div>

        <motion.div className="bg-gradient-to-br from-white/5 to-white/[0.02] border border-white/10 rounded-2xl p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <h2 className="text-xl font-semibold text-white mb-4">Quick Start</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a href="#docs" className="flex items-center gap-3 p-4 bg-white/5 rounded-xl hover:bg-white/10 border border-white/5"><ExternalLink className="w-5 h-5 text-purple-400" /><span className="text-white">Documentation</span></a>
            <a href="#demo" className="flex items-center gap-3 p-4 bg-white/5 rounded-xl hover:bg-white/10 border border-white/5"><ExternalLink className="w-5 h-5 text-purple-400" /><span className="text-white">Demo Store</span></a>
          </div>
        </motion.div>
        {onClose && <button onClick={onClose} className="mt-6 text-gray-400 hover:text-white text-sm mx-auto block">← Back</button>}
      </div>

      {showNewKeyModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div className="bg-[#0a0a0f] border border-white/10 rounded-2xl p-6 max-w-md w-full" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
            {!newKeyValue ? (<><h3 className="text-xl font-semibold text-white mb-4">Create API Key</h3><div className="space-y-4"><div><label className="block text-sm text-gray-400 mb-2">Name</label><input type="text" value={newKeyName} onChange={e => setNewKeyName(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white" placeholder="My API Key" /></div><div><label className="block text-sm text-gray-400 mb-2">Environment</label><select value={newKeyEnv} onChange={e => setNewKeyEnv(e.target.value as 'test' | 'live')} className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white"><option value="test">Test</option><option value="live">Live</option></select></div><div className="flex gap-3"><button onClick={() => setShowNewKeyModal(false)} className="flex-1 bg-white/5 text-white py-3 rounded-xl">Cancel</button><button onClick={handleCreateKey} className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-xl">Create</button></div></div></>) : (<><div className="text-center"><Check className="w-12 h-12 text-green-400 mx-auto mb-4" /><h3 className="text-xl font-semibold text-white mb-2">Key Created!</h3><p className="text-gray-400 text-sm mb-4">Copy now - won't be shown again</p></div><div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 mb-4"><code className="text-green-400 text-sm break-all">{newKeyValue}</code></div><div className="flex gap-3"><button onClick={() => copyToClipboard(newKeyValue)} className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-xl flex items-center justify-center gap-2"><Copy className="w-4 h-4" /> Copy</button><button onClick={() => { setShowNewKeyModal(false); setNewKeyValue(""); }} className="flex-1 bg-white/5 text-white py-3 rounded-xl">Done</button></div></>)}
          </motion.div>
        </div>
      )}
    </section>
  );
}
