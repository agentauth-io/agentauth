import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    storageKey: 'agentauth-session',  // Custom storage key
    storage: window.localStorage,      // Use localStorage for persistence
  }
});

// Types
export interface Developer {
  id: string;
  user_id: string;
  email: string;
  name?: string;
  company?: string;
  phone?: string;
  created_at: string;
}

export interface ApiKey {
  id: string;
  developer_id: string;
  key_prefix: string;
  key_hash: string;
  name: string;
  environment: 'test' | 'live';
  created_at: string;
  revoked_at?: string;
  last_used_at?: string;
}

// Auth helpers
export async function signUp(email: string, password: string, metadata?: { name?: string; company?: string; phone?: string }) {
  return await supabase.auth.signUp({ email, password, options: { data: metadata } });
}

export async function signIn(email: string, password: string) {
  return await supabase.auth.signInWithPassword({ email, password });
}

export async function signInWithGoogle() {
  return await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: window.location.origin },
  });
}

export async function signInWithGithub() {
  return await supabase.auth.signInWithOAuth({
    provider: 'github',
    options: { redirectTo: window.location.origin },
  });
}

export async function signOut() {
  localStorage.removeItem('agentauth-session');
  return await supabase.auth.signOut();
}

export async function getSession() {
  const { data: { session } } = await supabase.auth.getSession();
  return session;
}

// Developer helpers
export async function getDeveloper(userId: string): Promise<Developer | null> {
  const { data, error } = await supabase.from('developers').select('*').eq('user_id', userId).single();
  if (error && error.code !== 'PGRST116') console.error('getDeveloper error:', error);
  return data;
}

export async function createDeveloper(userId: string, email: string, metadata?: { name?: string; company?: string; phone?: string }): Promise<Developer | null> {
  const { data, error } = await supabase.from('developers').insert([{
    user_id: userId,
    email,
    name: metadata?.name,
    company: metadata?.company,
    phone: metadata?.phone
  }]).select().single();
  if (error) console.error('createDeveloper error:', error);
  return data;
}

// API Key helpers
export async function getApiKeys(developerId: string): Promise<ApiKey[]> {
  const { data, error } = await supabase
    .from('api_keys')
    .select('*')
    .eq('developer_id', developerId)
    .is('revoked_at', null)
    .order('created_at', { ascending: false });
  if (error) console.error('getApiKeys error:', error);
  return data || [];
}

export async function createApiKey(developerId: string, keyData: { key_prefix: string; key_hash: string; name: string; environment: 'test' | 'live' }): Promise<ApiKey | null> {
  const { data, error } = await supabase.from('api_keys').insert([{
    developer_id: developerId,
    ...keyData
  }]).select().single();
  if (error) console.error('createApiKey error:', error);
  return data;
}

export async function revokeApiKey(keyId: string): Promise<boolean> {
  const { error } = await supabase.from('api_keys').update({ revoked_at: new Date().toISOString() }).eq('id', keyId);
  if (error) console.error('revokeApiKey error:', error);
  return !error;
}

// Local storage helpers for API keys when DB not set up
const LOCAL_KEYS_KEY = 'agentauth-local-keys';

export function getLocalApiKeys(): ApiKey[] {
  try {
    const stored = localStorage.getItem(LOCAL_KEYS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch { return []; }
}

export function saveLocalApiKeys(keys: ApiKey[]): void {
  localStorage.setItem(LOCAL_KEYS_KEY, JSON.stringify(keys));
}

// Waitlist / Beta Access helpers
export interface WaitlistEntry {
  id: string;
  email: string;
  name?: string;
  status: 'pending' | 'approved' | 'rejected';
  beta_access: boolean;
  invite_code: string;
  created_at: string;
  approved_at?: string;
}

export async function checkBetaAccess(email: string): Promise<boolean> {
  if (!email) return false;
  const normalizedEmail = email.toLowerCase().trim();
  
  const { data, error } = await supabase
    .from('waitlist')
    .select('beta_access')
    .eq('email', normalizedEmail)
    .single();
  
  if (error && error.code !== 'PGRST116') {
    console.error('checkBetaAccess error:', error);
  }
  
  return data?.beta_access === true;
}

export async function getWaitlistEntry(email: string): Promise<WaitlistEntry | null> {
  if (!email) return null;
  const normalizedEmail = email.toLowerCase().trim();
  
  const { data, error } = await supabase
    .from('waitlist')
    .select('*')
    .eq('email', normalizedEmail)
    .single();
  
  if (error && error.code !== 'PGRST116') {
    console.error('getWaitlistEntry error:', error);
  }
  
  return data;
}

// Store beta access status in localStorage for quick navbar checks
const BETA_ACCESS_KEY = 'agentauth-beta-access';

export function setBetaAccessLocal(hasAccess: boolean): void {
  localStorage.setItem(BETA_ACCESS_KEY, hasAccess ? 'true' : 'false');
}

export function getBetaAccessLocal(): boolean {
  return localStorage.getItem(BETA_ACCESS_KEY) === 'true';
}

export function clearBetaAccessLocal(): void {
  localStorage.removeItem(BETA_ACCESS_KEY);
}
