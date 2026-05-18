function localSignupIntent(cta) {
  const email = window.prompt('Enter email to get early access and unlocks:');
  if (!email) return;
  const key = 'khatakshetra_signups';
  const existing = JSON.parse(localStorage.getItem(key) || '[]');
  existing.push({ email, cta, captured_at: new Date().toISOString() });
  localStorage.setItem(key, JSON.stringify(existing));
  window.alert('You are in. We will connect this to Supabase for production capture.');
}
