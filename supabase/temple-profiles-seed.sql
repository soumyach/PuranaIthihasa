-- Seed the 10 launch temples into temple_profiles so user_tips.temple_id
-- (FK -> temple_profiles.id) is satisfied. Authored temple GUIDE content stays
-- in /content/temple-guides.json (static pages); this table holds just the
-- identity row + community tips/freshness. Idempotent. Run after schema.sql.
insert into public.temple_profiles (id, slug, name, city, state, country) values
  ('tirumala-venkateswara', 'tirumala-venkateswara', 'Tirumala Venkateswara Temple', 'Tirupati', 'Andhra Pradesh', 'India'),
  ('kashi-vishwanath',      'kashi-vishwanath',      'Kashi Vishwanath Temple',      'Varanasi', 'Uttar Pradesh',  'India'),
  ('jagannath-puri',        'jagannath-puri',        'Jagannath Temple',             'Puri',     'Odisha',         'India'),
  ('meenakshi-amman',       'meenakshi-amman',       'Meenakshi Amman Temple',       'Madurai',  'Tamil Nadu',     'India'),
  ('ramanathaswamy',        'ramanathaswamy',        'Ramanathaswamy Temple',        'Rameswaram','Tamil Nadu',    'India'),
  ('somnath',               'somnath',               'Somnath Temple',               'Somnath',  'Gujarat',        'India'),
  ('mahakaleshwar',         'mahakaleshwar',         'Mahakaleshwar Temple',         'Ujjain',   'Madhya Pradesh', 'India'),
  ('siddhivinayak',         'siddhivinayak',         'Siddhivinayak Temple',         'Mumbai',   'Maharashtra',    'India'),
  ('kamakhya',              'kamakhya',              'Kamakhya Temple',              'Guwahati', 'Assam',          'India'),
  ('sabarimala',            'sabarimala',            'Sabarimala',                   'Pathanamthitta', 'Kerala',   'India')
on conflict (id) do nothing;
