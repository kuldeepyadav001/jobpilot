import { Link } from 'react-router-dom'
import { ArrowRight, Sparkles, Radar, FileSearch, Mail, Gauge, Rocket } from 'lucide-react'

const FEATURES = [
  { icon: Radar, title: 'Auto Scrape', desc: 'Internshala & Naukri on a timer — zero manual scrolling.' },
  { icon: FileSearch, title: 'Smart Matching', desc: 'Scores every job against your resumes and picks the best one.' },
  { icon: Sparkles, title: 'AI Cover Letters', desc: 'Local LLM writes a tailored letter for every application.' },
  { icon: Mail, title: 'Response Tracking', desc: 'Reads your inbox and auto-updates the pipeline status.' },
  { icon: Gauge, title: 'Live Health Check', desc: 'A lightweight in-app status indicator — no heavy monitoring containers.' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#07060f] text-white relative overflow-hidden flex flex-col">
      {/* Cinematic animated background (pure CSS/SVG, no heavy assets) */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(124,92,246,0.35),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_40%_40%_at_85%_60%,rgba(20,184,166,0.20),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_35%_35%_at_10%_80%,rgba(59,130,246,0.18),transparent_60%)]" />
        {/* swirling field lines */}
        <svg className="absolute inset-0 w-full h-full opacity-30" viewBox="0 0 1200 700" preserveAspectRatio="none">
          {[120, 200, 280, 360, 440, 520].map((r, i) => (
            <ellipse key={r} cx="600" cy="330" rx={r + 40} ry={r * 0.42} fill="none"
              stroke="url(#lg)" strokeWidth="1.4"
              transform={`rotate(${i * 8 - 32} 600 330)`} opacity={0.5 + i * 0.08} />
          ))}
          <defs>
            <linearGradient id="lg" x1="0" x2="1">
              <stop offset="0" stopColor="#8b7bf7" stopOpacity="0.5" />
              <stop offset="0.5" stopColor="#9a8cff" stopOpacity="0.1" />
              <stop offset="1" stopColor="#14b8a6" stopOpacity="0.5" />
            </linearGradient>
          </defs>
        </svg>
        {/* subtle grain */}
        <div className="absolute inset-0 opacity-[0.05] mix-blend-overlay"
          style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27120%27 height=%27120%27%3E%3Cfilter id=%27n%27%3E%3CfeTurbulence type=%27fractalNoise%27 baseFrequency=%270.9%27 numOctaves=%272%27/%3E%3C/filter%3E%3Crect width=%27100%25%27 height=%27100%25%27 filter=%27url(%23n)%27 opacity=%270.6%27/%3E%3C/svg%3E")' }} />
      </div>

      {/* Top nav */}
      <header className="relative z-10 flex items-center justify-between px-6 md:px-12 py-5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-teal-400 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-bold tracking-tight">JobPilot</span>
        </div>
        <nav className="hidden md:flex items-center gap-8 text-sm text-white/70">
          <span className="hover:text-white cursor-pointer transition">How It Works</span>
          <span className="hover:text-white cursor-pointer transition">Features</span>
          <span className="hover:text-white cursor-pointer transition">Pricing</span>
          <span className="hover:text-white cursor-pointer transition">Support</span>
        </nav>
        <Link to="/dashboard" className="btn-primary !bg-white !text-[#1a1030] hover:!bg-white/90 text-sm px-5 py-2.5">
          <Rocket className="w-4 h-4" /> Launch Dashboard
        </Link>
      </header>

      {/* Hero */}
      <main className="relative z-10 flex-1 flex flex-col justify-center px-6 md:px-12 pb-16">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-violet-200 bg-white/5 border border-white/10 rounded-full px-3 py-1 mb-6">
            <Sparkles className="w-3.5 h-3.5" /> Fully automated job hunting
          </div>
          <h1 className="text-5xl md:text-7xl font-black tracking-tight leading-[1.05]">
            JobPilot
          </h1>
          <p className="mt-3 text-2xl md:text-3xl font-semibold text-white/70 tracking-tight">
            Where applications begin.
          </p>
          <p className="mt-6 text-white/55 text-base md:text-lg max-w-lg leading-relaxed">
            Stop scrolling job portals. JobPilot scrapes, scores, writes, applies, and tracks —
            running the whole loop on your machine, so you only open the dashboard to see results.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link to="/dashboard" className="btn-primary !bg-white !text-[#1a1030] hover:!bg-white/90 text-base px-7 py-3.5">
              Start Exploring <ArrowRight className="w-4 h-4" />
            </Link>
            <span className="text-xs text-white/40">Local-first · No cloud · 100% free</span>
          </div>
        </div>

        {/* Feature cards */}
        <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 max-w-5xl">
          {FEATURES.map((f) => (
            <div key={f.title} className="bg-white/5 border border-white/10 rounded-2xl p-4 backdrop-blur-sm hover:bg-white/8 transition">
              <f.icon className="w-5 h-5 text-violet-300 mb-3" />
              <p className="text-sm font-bold">{f.title}</p>
              <p className="text-xs text-white/50 mt-1 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </main>

      <footer className="relative z-10 px-6 md:px-12 py-5 flex items-center justify-between text-xs text-white/40">
        <span>The loop runs itself. You run the chase.</span>
        <span className="flex items-center gap-2"><BrandNote /> JobPilot © 2025</span>
      </footer>
    </div>
  )
}

function BrandNote() {
  return <span className="w-4 h-4 rounded bg-gradient-to-br from-violet-500 to-teal-400 inline-block" />
}
