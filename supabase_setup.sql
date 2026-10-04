-- Run this once in Supabase: SQL Editor -> New query -> Run
create table if not exists events (
  id bigint generated always as identity primary key,
  detected_at timestamptz default now(),
  image_file text,
  email_status text
);

alter table events enable row level security;

create policy "allow insert" on events for insert to anon with check (true);
create policy "allow read" on events for select to anon using (true);
