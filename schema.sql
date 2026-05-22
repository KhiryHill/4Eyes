-- Run this in your Supabase SQL editor to set up the database

-- Users table
create table if not exists users (
  id uuid default gen_random_uuid() primary key,
  email text unique not null,
  password text not null,
  name text default '',
  created_at timestamp default now()
);

-- Prescriptions table
create table if not exists prescriptions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references users(id) on delete cascade,
  right_sph float default 0,
  right_cyl float default 0,
  right_axis int default 90,
  left_sph float default 0,
  left_cyl float default 0,
  left_axis int default 90,
  add_val float default 0,
  updated_at timestamp default now()
);

-- Settings table
create table if not exists settings (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references users(id) on delete cascade,
  brightness int default 60,
  scale float default 1.0,
  contrast float default 1.0,
  spacing int default 0,
  line_height float default 1.6,
  updated_at timestamp default now()
);

-- Indexes for fast lookups
create index if not exists idx_prescriptions_user on prescriptions(user_id);
create index if not exists idx_settings_user on settings(user_id);
create index if not exists idx_users_email on users(email);
