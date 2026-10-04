-- Every collection's records, as JSON (see lib/db/postgres.ts). Run once on your database
-- (Supabase: SQL editor; Docker: applied by docker-compose on first start).
create table if not exists documents (
  id uuid primary key,
  collection text not null,
  data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists documents_collection_created on documents (collection, created_at desc);
create index if not exists documents_data on documents using gin (data);

-- Only the server (with the database password) reads and writes; nothing is public.
alter table documents enable row level security;
