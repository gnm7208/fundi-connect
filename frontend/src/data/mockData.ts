export type FundiProfile = {
  id: number
  name: string
  businessName: string
  city: string
  estate: string
  rating: number
  jobsCompleted: number
  skill: string
  category: string
  hourlyRate: number
  distanceKm: number
  verified: boolean
  responseTime: string
  bio: string
}

export type Booking = {
  id: number
  title: string
  customer: string
  date: string
  status: 'Requested' | 'Accepted' | 'In progress' | 'Completed'
  amount: string
  fundi: string
}

export const MOCK_FUNDIS: FundiProfile[] = [
  {
    id: 1,
    name: 'Mwangi Kibet',
    businessName: 'Kilimani Fix Works',
    city: 'Nairobi',
    estate: 'Kilimani',
    rating: 4.9,
    jobsCompleted: 142,
    skill: 'Plumbing & Drainage',
    category: 'Plumbing',
    hourlyRate: 2500,
    distanceKm: 2.4,
    verified: true,
    responseTime: '12 mins',
    bio: 'Same-day plumbing repairs, pipe reroutes, and kitchen installation for apartments and offices.',
  },
  {
    id: 2,
    name: 'Amina Salim',
    businessName: 'Eastern Wiring Co.',
    city: 'Nairobi',
    estate: 'Eastleigh',
    rating: 4.8,
    jobsCompleted: 96,
    skill: 'Electrical Repairs',
    category: 'Electrical',
    hourlyRate: 3000,
    distanceKm: 5.1,
    verified: true,
    responseTime: '18 mins',
    bio: 'Trusted for lighting faults, panel upgrades, and appliance troubleshooting across Nairobi estates.',
  },
  {
    id: 3,
    name: 'Daniel Otieno',
    businessName: 'Muthaiga Carpentry Studio',
    city: 'Nairobi',
    estate: 'Muthaiga',
    rating: 4.7,
    jobsCompleted: 68,
    skill: 'Carpentry & Furniture',
    category: 'Carpentry',
    hourlyRate: 2200,
    distanceKm: 6.8,
    verified: true,
    responseTime: '27 mins',
    bio: 'Custom cabinet repairs, hinges, and wooden furniture touch-ups for homes and small businesses.',
  },
]

export const MOCK_BOOKINGS: Booking[] = [
  {
    id: 101,
    title: 'Bathroom pipe leak',
    customer: 'Jane W.',
    date: 'Today, 10:30 AM',
    status: 'Accepted',
    amount: 'KES 4,800',
    fundi: 'Mwangi Kibet',
  },
  {
    id: 102,
    title: 'Office lighting fix',
    customer: 'Kibaki Tech',
    date: 'Tomorrow, 8:15 AM',
    status: 'In progress',
    amount: 'KES 6,000',
    fundi: 'Amina Salim',
  },
  {
    id: 103,
    title: 'Cabinet hinge repair',
    customer: 'Lucy T.',
    date: 'Wed, 2:00 PM',
    status: 'Completed',
    amount: 'KES 3,900',
    fundi: 'Daniel Otieno',
  },
]
