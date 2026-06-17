// Exposes the PUBLIC Supabase config to the browser (added for P1-1).
// The anon key is designed to be public — it is safe to expose IF Row-Level
// Security is enabled (see supabase/rls-policies.sql). The service-role key is
// NEVER sent here; it stays server-only in /api/email-capture and /api/event.
// Until SUPABASE_URL + SUPABASE_ANON_KEY are set in Vercel, this returns
// { configured: false } and the client-side auth/sync no-ops gracefully.
export default function handler(req, res) {
  const supabaseUrl = process.env.SUPABASE_URL || '';
  const supabaseAnonKey = process.env.SUPABASE_ANON_KEY || '';
  res.setHeader('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=600');
  return res.status(200).json({
    configured: Boolean(supabaseUrl && supabaseAnonKey),
    supabaseUrl: supabaseUrl,
    supabaseAnonKey: supabaseAnonKey
  });
}
