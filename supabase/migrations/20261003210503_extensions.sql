-- Extensions live in the `extensions` schema (Supabase convention).
create extension if not exists vector with schema extensions;
create extension if not exists pgcrypto with schema extensions;
