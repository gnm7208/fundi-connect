import { useEffect, useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { MapPin, Search, SearchX, SlidersHorizontal } from 'lucide-react'

import { Button, EmptyState, SkeletonList } from '@/components/ui'
import { FundiCard } from '@/features/fundis/FundiCard'
import { api, type FundiSearchParams } from '@/lib/api'

type Sort = NonNullable<FundiSearchParams['sort']>

const SORTS: { value: Sort; label: string }[] = [
  { value: 'rating', label: 'Top rated' },
  { value: 'distance', label: 'Nearest' },
  { value: 'jobs', label: 'Most jobs' },
  { value: 'rate_asc', label: 'Lowest rate' },
]

export function FundiSearchPage() {
  const [term, setTerm] = useState('')
  const [debouncedTerm, setDebouncedTerm] = useState('')
  const [category, setCategory] = useState<string>('')
  const [sort, setSort] = useState<Sort>('rating')
  const [verifiedOnly, setVerifiedOnly] = useState(false)
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null)
  const [locating, setLocating] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedTerm(term.trim()), 280)
    return () => clearTimeout(timer)
  }, [term])

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => api.categories.list(),
    staleTime: 5 * 60_000,
  })

  const { data, isPending, isError } = useQuery({
    queryKey: ['fundis', debouncedTerm, category, sort, verifiedOnly, coords],
    queryFn: () =>
      api.fundis.search({
        q: debouncedTerm || undefined,
        category: category || undefined,
        sort,
        verified_only: verifiedOnly || undefined,
        lat: coords?.lat,
        lng: coords?.lng,
        radius_km: coords ? 25 : undefined,
        per_page: 24,
      }),
    // Keeps the previous results on screen while a filter change loads, so the
    // list does not collapse to skeletons on every keystroke.
    placeholderData: keepPreviousData,
  })

  function useMyLocation() {
    if (!navigator.geolocation) return
    setLocating(true)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({ lat: position.coords.latitude, lng: position.coords.longitude })
        setSort('distance')
        setLocating(false)
      },
      () => setLocating(false),
      { timeout: 8000 },
    )
  }

  const fundis = data?.fundis ?? []

  return (
    <div className="stack-lg">
      <div className="page-head">
        <h1>Find a fundi</h1>
        <p className="muted">Verified craftspeople near you, paid through escrow.</p>
      </div>

      <div className="card stack">
        <div className="row" style={{ position: 'relative' }}>
          <Search
            size={16}
            aria-hidden
            style={{
              position: 'absolute',
              left: 12,
              color: 'var(--text-subtle)',
              pointerEvents: 'none',
            }}
          />
          <input
            className="input"
            style={{ paddingLeft: 36 }}
            type="search"
            placeholder="Search plumber, electrician, name or estate…"
            value={term}
            onChange={(event) => setTerm(event.target.value)}
            aria-label="Search fundis"
          />
          <Button onClick={useMyLocation} loading={locating}>
            <MapPin size={15} />
            {coords ? 'Near me' : 'Use location'}
          </Button>
        </div>

        <div className="chip-row">
          <button className="chip" aria-pressed={category === ''} onClick={() => setCategory('')}>
            All trades
          </button>
          {categories?.map((item) => (
            <button
              key={item.id}
              className="chip"
              aria-pressed={category === item.slug}
              onClick={() => setCategory(category === item.slug ? '' : item.slug)}
            >
              {item.name}
            </button>
          ))}
        </div>

        <div className="row wrap" style={{ justifyContent: 'space-between' }}>
          <div className="row wrap">
            <SlidersHorizontal size={14} className="muted" aria-hidden />
            {SORTS.map((option) => (
              <button
                key={option.value}
                className="chip"
                aria-pressed={sort === option.value}
                onClick={() => setSort(option.value)}
                disabled={option.value === 'distance' && !coords}
                title={
                  option.value === 'distance' && !coords
                    ? 'Share your location to sort by distance'
                    : undefined
                }
              >
                {option.label}
              </button>
            ))}
          </div>
          <button
            className="chip"
            aria-pressed={verifiedOnly}
            onClick={() => setVerifiedOnly((value) => !value)}
          >
            Verified only
          </button>
        </div>
      </div>

      {isPending ? (
        <SkeletonList count={6} />
      ) : isError ? (
        <EmptyState
          icon={<SearchX size={20} />}
          title="Could not load fundis"
          description="Check your connection and try again."
        />
      ) : fundis.length === 0 ? (
        <EmptyState
          icon={<SearchX size={20} />}
          title="No fundis match that"
          description="Try a different trade, or widen your search by clearing filters."
          action={
            <Button
              onClick={() => {
                setTerm('')
                setCategory('')
                setVerifiedOnly(false)
              }}
            >
              Clear filters
            </Button>
          }
        />
      ) : (
        <>
          <p className="subtle">
            {data.count} fundi{data.count === 1 ? '' : 's'} available
          </p>
          <div className="grid-cards stagger">
            {fundis.map((fundi) => (
              <FundiCard key={fundi.id} fundi={fundi} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
