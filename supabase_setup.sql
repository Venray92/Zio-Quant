-- Z-QUANT: tabel penyimpanan data pengguna (watchlist, portofolio, setelan).
-- Cara pakai: Supabase > SQL Editor > New query > paste semua isi file ini > Run.

create table if not exists public.user_data (
  user_id    text        not null,
  kind       text        not null,
  data       jsonb       not null default '[]'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (user_id, kind)
);

-- Pengaman: RLS aktif TANPA policy, jadi kunci publik (publishable) tidak bisa membaca
-- atau menulis apa pun. App mengakses data dari server (Streamlit) memakai secret key,
-- yang memang melewati RLS.
alter table public.user_data enable row level security;
