-- RAG corpus: sources + chunked passages with e5-small embeddings (384 dims).
-- Embeddings are computed client-side (Python) with intfloat/multilingual-e5-small:
--   ingestion -> "passage: <text>", query -> "query: <text>", normalized vectors.

create table public.sources (
  id           uuid primary key default gen_random_uuid(),
  kind         text not null
               check (kind in ('official_doc','questionnaire','data_dictionary','sampling_design','paper','report','internal')),
  title        text not null,
  url          text,
  doi          text,
  publisher    text,
  year         int,
  license      text,
  is_demo      boolean not null default false,
  retrieved_at timestamptz not null default now(),
  constraint sources_url_key unique (url)
);

create table public.passages (
  id         uuid primary key default gen_random_uuid(),
  source_id  uuid not null references public.sources(id) on delete cascade,
  section    text,
  locator    text not null,   -- e.g. 'p. 12' or 'chunk 4'
  content    text not null,
  embedding  extensions.vector(384),
  -- 'simple' config: corpus mixes Spanish and English.
  fts        tsvector generated always as (
               to_tsvector('simple', coalesce(section, '') || ' ' || content)
             ) stored,
  created_at timestamptz not null default now(),
  constraint passages_source_locator_key unique (source_id, locator)
);
create index passages_source_idx on public.passages(source_id);
create index passages_fts_idx on public.passages using gin (fts);
create index passages_embedding_idx on public.passages
  using hnsw (embedding extensions.vector_cosine_ops);

-- Hybrid search with Reciprocal Rank Fusion (Supabase hybrid-search guide),
-- returning everything needed to cite a passage.
create or replace function public.hybrid_search(
  query_text       text,
  query_embedding  extensions.vector(384),
  match_count      int   default 5,
  full_text_weight float default 1,
  semantic_weight  float default 1,
  rrf_k            int   default 50
)
returns table (
  passage_id    uuid,
  source_id     uuid,
  source_title  text,
  source_kind   text,
  url           text,
  doi           text,
  section       text,
  locator       text,
  content       text,
  score         float
)
language sql
stable
security invoker
set search_path = public, extensions
as $$
  with full_text as (
    select p.id,
           row_number() over (
             order by ts_rank_cd(p.fts, websearch_to_tsquery('simple', query_text)) desc
           ) as rank_ix
    from public.passages p
    where p.fts @@ websearch_to_tsquery('simple', query_text)
    order by rank_ix
    limit least(match_count, 30) * 2
  ),
  semantic as (
    select p.id,
           row_number() over (order by p.embedding <=> query_embedding) as rank_ix
    from public.passages p
    where p.embedding is not null
    order by rank_ix
    limit least(match_count, 30) * 2
  ),
  fused as (
    select coalesce(ft.id, s.id) as id,
           coalesce(1.0 / (rrf_k + ft.rank_ix), 0.0) * full_text_weight +
           coalesce(1.0 / (rrf_k + s.rank_ix), 0.0) * semantic_weight as score
    from full_text ft
    full outer join semantic s on ft.id = s.id
  )
  select p.id, src.id, src.title, src.kind, src.url, src.doi,
         p.section, p.locator, p.content, f.score::float
  from fused f
  join public.passages p on p.id = f.id
  join public.sources src on src.id = p.source_id
  order by f.score desc
  limit least(match_count, 30);
$$;
