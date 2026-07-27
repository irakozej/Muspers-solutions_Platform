// MusperSolutions, content data extracted from the existing site
// (reference/muspersolutions.com/index.html). Tweak copy here, not in components.

export const brand = {
  name: 'MusperSolutions',
  legalName: 'MusperSolutions Ltd',
  tagline: 'Equipping businesses to scale through strategy and systems.',
  location: 'Kigali, Rwanda',
  founded: 2011,
};

export const contactInfo = {
  email: 'info@muspersolutions.com',
  phone: '+250 788 300 840',
  whatsapp: 'https://api.whatsapp.com/send/?phone=250788300840',
  address: {
    line1: 'KN 12, Nyarugenge',
    line2: 'Kigali, Rwanda',
  },
  socials: [
    { label: 'LinkedIn', href: 'https://www.linkedin.com/in/musper-solutions' },
    { label: 'Instagram', href: 'https://www.instagram.com/muspersolutions' },
    { label: 'Twitter', href: 'https://twitter.com/muspersolutions' },
  ],
};

export const stats = [
  { value: '2000+', label: 'Entrepreneurs trained', detail: 'across Rwanda and the region' },
  { value: '15+', label: 'Years of practice', detail: 'in private-sector development' },
  { value: '45+', label: 'Institutional clients', detail: 'banks, MFIs, NGOs, government' },
  { value: '10', label: 'Awards & recognitions', detail: 'for impact and delivery' },
];

export const services = [
  {
    id: 'advisory',
    number: '01',
    title: 'Business Development Advisory',
    summary:
      'Diagnose what is holding a business back, then build the strategy, systems, and financial discipline to scale.',
    points: [
      'Business diagnostics',
      'Growth strategy development',
      'Financial management systems',
      'Pricing and costing support',
      'Investment readiness preparation',
    ],
    outcome: 'A measurable roadmap from where you are to investment-ready.',
    image:
      'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?auto=format&fit=crop&w=1400&q=80',
    imageAlt: 'A business advisory meeting in session',
  },
  {
    id: 'capacity',
    number: '02',
    title: 'Entrepreneurship & Capacity Building',
    summary:
      'ILO-certified training and mentorship programs that equip founders with the practical skills to start and run profitable businesses.',
    points: [
      'ILO Start and Improve Your Business (SIYB)',
      'Entrepreneurship Training of Trainers',
      'Business mentorship programs',
      'Women entrepreneurship programs',
      'SME growth workshops',
    ],
    outcome: 'Founders who can move from idea to operating business, and trainers who can multiply the impact.',
    image:
      'https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=1400&q=80',
    imageAlt: 'A training workshop with adult learners',
  },
  {
    id: 'fi-programs',
    number: '03',
    title: 'SME Programs for Financial Institutions',
    summary:
      'Helping banks, MFIs, and SACCOs strengthen their SME portfolios through structured advisory and capacity building.',
    points: [
      'SME client training programs',
      'Financial literacy programs',
      'SME advisory clinics',
      'Portfolio strengthening initiatives',
    ],
    outcome: 'Better-prepared borrowers, healthier portfolios, deeper relationships with SME clients.',
    image:
      'https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1400&q=80',
    imageAlt: 'A financial advisory desk with documents and calculations',
  },
  {
    id: 'events',
    number: '04',
    title: 'Business Events & Ecosystem Convenings',
    summary:
      'Designing and delivering forums, networking events, and sector dialogues that move conversations into action.',
    points: [
      'Business forums',
      'B2B networking events',
      'Entrepreneurship conferences',
      'Sector dialogues',
    ],
    outcome: 'Convenings that create the introductions, deals, and partnerships your sector needs.',
    image:
      'https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=1400&q=80',
    imageAlt: 'A panel discussion at a business conference',
  },
  {
    id: 'institutional',
    number: '05',
    title: 'Institutional Advisory',
    summary:
      'For development partners, governments, and NGOs delivering entrepreneurship and private-sector programs.',
    points: [
      'Programme design',
      'Entrepreneurship ecosystem analysis',
      'Funding landscape mapping',
      'Monitoring and evaluation support',
    ],
    outcome: 'Programs grounded in evidence, designed for the realities on the ground.',
    image:
      'https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1400&q=80',
    imageAlt: 'A formal strategy meeting in an institutional setting',
  },
];

export const programs = [
  {
    id: 'siyb',
    name: 'SIYB Rwanda Hub',
    eyebrow: 'Flagship · ILO-certified',
    summary:
      'The Rwandan hub for the International Labour Organization\'s Start and Improve Your Business (SIYB) methodology, a global standard for entrepreneurship training, adapted for the local market.',
    audience: 'Aspiring entrepreneurs, early-stage founders, and trainers who want to become certified SIYB facilitators.',
    outcomes: [
      'Move from a business idea to a documented business plan',
      'Master practical bookkeeping, costing, and cash flow',
      'Build the operational discipline to grow profitably',
    ],
  },
  {
    id: 'growth-clinics',
    name: 'SME Growth Clinics',
    eyebrow: 'Cohort · 12 weeks',
    summary:
      'Intensive, advisory-led clinics for growing SMEs ready to professionalize. A combination of group sessions, one-on-one diagnostics, and accountability check-ins.',
    audience: 'Established SMEs (typically 2+ years, with revenue) ready to invest in systems, financial discipline, and growth strategy.',
    outcomes: [
      'A signed-off growth strategy with quarterly targets',
      'A clean monthly financial dashboard',
      'A pipeline of investment, partnership, or market opportunities',
    ],
  },
  {
    id: 'women-digital',
    name: 'Women in Digital Business',
    eyebrow: 'Cohort · 8 weeks',
    summary:
      'A practical, hands-on program for women entrepreneurs building or scaling businesses with a digital component, from e-commerce to digital services.',
    audience: 'Women founders and business owners who want to grow through digital channels, online sales, digital marketing, payments, and tools.',
    outcomes: [
      'A working online storefront or service offering',
      'A digital marketing playbook tailored to the business',
      'A peer network of women entrepreneurs across sectors',
    ],
  },
];

export const testimonials = [
  {
    quote:
      'MusperSolutions provided practical guidance that helped us improve how we manage our business operations and plan for growth. Their approach is professional and very supportive to entrepreneurs.',
    name: 'SME Entrepreneur',
    role: 'Entrepreneur support engagement',
  },
  {
    quote:
      'The advisory sessions were insightful and solution-oriented. We gained valuable tools for better financial management and strategic planning for our business.',
    name: 'Small Business Owner',
    role: 'Business advisory engagement',
  },
  {
    quote:
      'The training and mentorship we received strengthened our understanding of business development and market opportunities. MusperSolutions is truly committed to supporting entrepreneurs.',
    name: 'Startup Founder',
    role: 'Capacity-building cohort',
  },
  {
    quote:
      'The digital business support helped us explore new ways to reach customers and improve our visibility online. It has been a valuable experience for our business growth.',
    name: 'Women Entrepreneur',
    role: 'Women in Digital Business program',
  },
];

export const values = [
  {
    title: 'Integrity',
    body: 'We say what we will do, and we do it. No padding, no theatre.',
  },
  {
    title: 'Innovation',
    body: 'We adapt global methodologies to African realities, not the other way around.',
  },
  {
    title: 'Excellence',
    body: 'Every deliverable is one we would put our name on. Because we do.',
  },
  {
    title: 'Sustainability',
    body: 'We measure success in businesses that are still standing, growing, and hiring years later.',
  },
];

export const audiences = [
  {
    title: 'Entrepreneurs & SMEs',
    body: 'Growth-oriented businesses seeking structured advisory, mentorship, and systems to scale.',
  },
  {
    title: 'Financial Institutions',
    body: 'Banks, MFIs, and SACCOs strengthening SME portfolios through advisory and capacity building.',
  },
  {
    title: 'Development Partners',
    body: 'International organizations, NGOs, and programs implementing entrepreneurship and private-sector initiatives.',
  },
];

export const founder = {
  name: 'MusperSolutions Advisory',
  role: 'Founder & Chief Executive',
  blurb:
    'MusperSolutions exists to close the gap between high-potential African entrepreneurs and the systems, advisory, and capital they need to scale.',
  bio: [
    'Over 15+ years of practice across private-sector development, MusperSolutions has worked with banks, MFIs, development partners, government institutions, and hundreds of SMEs, from informal traders earning their first profits to growing companies preparing for investment.',
    'The approach is grounded and practical: globally recognized methodologies (including ILO\'s Start and Improve Your Business) paired with deep local context, staying close to the work until results show up on a balance sheet.',
    'The team has trained 2000+ entrepreneurs, designed SME programs for financial institutions, and advised development partners on the design of entrepreneurship initiatives across the region.',
  ],
};

// Photo URLs, curated to depict Black / African professionals in business contexts.
// All free-license on Unsplash, attribution not required.
// To replace any with a real photo: drop the file in frontend/public/ and change
// the URL here to '/your-filename.jpg' (same pattern as /penny.jpg).
export const images = {
  heroPortrait:
    'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=1400&q=80',
  kigaliSkyline:
    'https://images.unsplash.com/photo-1611348586804-61bf6c080437?auto=format&fit=crop&w=1600&q=80',
  workshop:
    'https://images.unsplash.com/photo-1573164713988-8665fc963095?auto=format&fit=crop&w=1400&q=80',
  meeting:
    'https://images.unsplash.com/photo-1543269865-cbf427effbad?auto=format&fit=crop&w=1400&q=80',
  marketplace:
    'https://images.unsplash.com/photo-1597393353415-b3730f3719fe?auto=format&fit=crop&w=1400&q=80',
  founderPortrait: '/penny.jpg',
  team:
    'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1600&q=80',
  growth:
    'https://images.unsplash.com/photo-1559523275-98fb3c56faf6?auto=format&fit=crop&w=1400&q=80',
  women:
    'https://images.unsplash.com/photo-1531123897727-8f129e1688ce?auto=format&fit=crop&w=1400&q=80',
  digital:
    'https://images.unsplash.com/photo-1604881991720-f91add269bed?auto=format&fit=crop&w=1400&q=80',
};

export const navLinks = [
  { to: '/', label: 'Home' },
  { to: '/about', label: 'About' },
  { to: '/services', label: 'Services' },
  { to: '/programs', label: 'Programs' },
  { to: '/testimonials', label: 'Voices' },
  { to: '/contact', label: 'Contact' },
];
