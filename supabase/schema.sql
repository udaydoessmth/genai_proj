create extension if not exists pgcrypto;

create table if not exists public.trips (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  destination text not null check (char_length(destination) between 2 and 120),
  budget_tier text not null check (budget_tier in ('Budget', 'Moderate', 'Luxury')),
  start_date date not null,
  end_date date not null,
  travel_style text not null check (travel_style in ('Solo', 'Couple', 'Family', 'Friends')),
  group_size integer not null check (group_size between 1 and 20),
  interests text[] not null default '{}',
  trip_summary text not null default '',
  total_estimated_cost text not null default '',
  created_at timestamptz not null default now(),
  constraint valid_trip_dates check (end_date >= start_date and end_date - start_date <= 30)
);

create table if not exists public.itineraries (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid not null references public.trips(id) on delete cascade,
  day_number integer not null check (day_number between 1 and 31),
  activities jsonb not null,
  created_at timestamptz not null default now(),
  unique (trip_id, day_number)
);

create index if not exists trips_user_created_idx
  on public.trips (user_id, created_at desc);
create index if not exists itineraries_trip_day_idx
  on public.itineraries (trip_id, day_number);

alter table public.trips enable row level security;
alter table public.itineraries enable row level security;

drop policy if exists "Users can read their own trips" on public.trips;
create policy "Users can read their own trips"
  on public.trips for select to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "Users can create their own trips" on public.trips;
create policy "Users can create their own trips"
  on public.trips for insert to authenticated
  with check ((select auth.uid()) = user_id);

drop policy if exists "Users can update their own trips" on public.trips;
create policy "Users can update their own trips"
  on public.trips for update to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

drop policy if exists "Users can delete their own trips" on public.trips;
create policy "Users can delete their own trips"
  on public.trips for delete to authenticated
  using ((select auth.uid()) = user_id);

drop policy if exists "Users can read itineraries for their trips" on public.itineraries;
create policy "Users can read itineraries for their trips"
  on public.itineraries for select to authenticated
  using (exists (
    select 1 from public.trips
    where trips.id = itineraries.trip_id
      and trips.user_id = (select auth.uid())
  ));

drop policy if exists "Users can create itineraries for their trips" on public.itineraries;
create policy "Users can create itineraries for their trips"
  on public.itineraries for insert to authenticated
  with check (exists (
    select 1 from public.trips
    where trips.id = itineraries.trip_id
      and trips.user_id = (select auth.uid())
  ));

drop policy if exists "Users can update itineraries for their trips" on public.itineraries;
create policy "Users can update itineraries for their trips"
  on public.itineraries for update to authenticated
  using (exists (
    select 1 from public.trips
    where trips.id = itineraries.trip_id
      and trips.user_id = (select auth.uid())
  ))
  with check (exists (
    select 1 from public.trips
    where trips.id = itineraries.trip_id
      and trips.user_id = (select auth.uid())
  ));

drop policy if exists "Users can delete itineraries for their trips" on public.itineraries;
create policy "Users can delete itineraries for their trips"
  on public.itineraries for delete to authenticated
  using (exists (
    select 1 from public.trips
    where trips.id = itineraries.trip_id
      and trips.user_id = (select auth.uid())
  ));
