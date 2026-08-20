/**
 * /api/diag tests — the endpoint answers "is the drip actually live?" without
 * anyone pasting a secret into a URL.  node tests/diag.test.mjs
 */
// Exercise /api/diag against a fake Supabase in the states that matter.
const results = []; const check = (n,p,d='') => results.push([p,n,d]);
const mod = await import('../api/diag.js');

function mkRes(){ const r={headers:{}}; r.setHeader=(k,v)=>{r.headers[k]=v;}; r.status=c=>{r.code=c;return r;}; r.json=b=>{r.body=b;return r;}; return r; }

async function run({ tableMissing = false, noCronSecret = false } = {}) {
  process.env.SUPABASE_URL='https://fake.supabase.co';
  process.env.SUPABASE_SERVICE_ROLE_KEY='k';
  process.env.GMAIL_CLIENT_ID='a'; process.env.GMAIL_CLIENT_SECRET='b'; process.env.GMAIL_REFRESH_TOKEN='c';
  if (noCronSecret) delete process.env.CRON_SECRET; else process.env.CRON_SECRET='s';
  global.fetch = async (u) => {
    const missing = tableMissing && /email_sends|email_subscriber_progress/.test(String(u));
    return missing
      ? { ok:false, status:404, text: async () => 'relation "public.email_sends" does not exist' }
      : { ok:true, text: async () => '' };
  };
  const res = mkRes(); await mod.default({}, res); return res.body;
}

let b = await run();
check('reports drip ready when everything is in place', b.dripReady === true, JSON.stringify(b.dripBlockedBy));
check('  → probes the new table and view', b.tables.email_sends === 'ok' && b.tables.email_subscriber_progress === 'ok');
check('  → confirms the drip modules import', b.dripModule === 'ok', b.dripModule);
check('  → reports CRON_SECRET presence as a boolean, never its value',
      b.env.CRON_SECRET === true && !JSON.stringify(b).includes('"s"'));

b = await run({ tableMissing: true });
check('SQL not run → not ready', b.dripReady === false);
check('  → and says exactly which step is missing',
      (b.dripBlockedBy||[]).some(x => /run supabase\/email-drip.sql/.test(x)), JSON.stringify(b.dripBlockedBy));

b = await run({ noCronSecret: true });
check('no CRON_SECRET → not ready, and says so',
      b.dripReady === false && (b.dripBlockedBy||[]).some(x => /CRON_SECRET/.test(x)), JSON.stringify(b.dripBlockedBy));

let fails=0; for (const [p,n,d] of results){ if(!p) fails++; console.log(`${p?'PASS':'FAIL'}  ${n}${!p&&d?'  → '+d:''}`); }
console.log(`\n${results.length-fails}/${results.length} passed`); process.exit(fails?1:0);
