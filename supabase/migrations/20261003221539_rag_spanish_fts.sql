-- RAG v2: Spanish full-text search and partial-match ranking.
-- Every passage is Spanish (OpenAlex papers are stored as metadata only, without passages), so:
--   * 'simple' had no stemming or accent folding: "traslados" did not match "traslado",
--     nor "dormir" match "durmió"; Spanish stopwords also counted as terms.
--   * websearch_to_tsquery ANDs every term, so most natural-language queries got zero
--     full-text hits and hybrid_search silently degraded to vector-only.
-- Now: Spanish stemming + unaccent, and the full-text leg matches ANY query term, ranking first by
-- how many distinct query terms a passage contains (coordination), then by ts_rank_cd.

create extension if not exists unaccent with schema extensions;

create text search configuration public.es_unaccent (copy = pg_catalog.spanish);
alter text search configuration public.es_unaccent
  alter mapping for hword, hword_part, word with extensions.unaccent, spanish_stem;

alter table public.passages drop column fts;
alter table public.passages add column fts tsvector generated always as (
  to_tsvector('public.es_unaccent'::regconfig, coalesce(section, '') || ' ' || content)
) stored;
create index passages_fts_idx on public.passages using gin (fts);

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
  with q as (
    select tsvector_to_array(to_tsvector('public.es_unaccent'::regconfig, query_text)) as terms,
           -- plainto_tsquery quotes lexemes safely; turning AND into OR keeps partial matches.
           nullif(replace(plainto_tsquery('public.es_unaccent'::regconfig, query_text)::text, ' & ', ' | '), '')::tsquery
             as any_term
  ),
  full_text as (
    select p.id,
           row_number() over (
             order by cardinality(array(
                        select unnest(tsvector_to_array(p.fts)) intersect select unnest(q.terms)
                      )) desc,
                      ts_rank_cd(p.fts, q.any_term) desc
           ) as rank_ix
    from public.passages p, q
    where p.fts @@ q.any_term
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
