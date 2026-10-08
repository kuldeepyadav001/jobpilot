import { Link } from 'react-router-dom'
import {
  ArrowRight, Radar, FileSearch, PenLine, Mail, Gauge,
  KeyRound, Workflow, CheckCircle2, Compass,
} from 'lucide-react'

const STEPS = [
  { icon: KeyRound, title: 'Connect', desc: 'Point it at your portals and drop in your resumes. No accounts, no cloud.' },
  { icon: Workflow, title: 'It works', desc: 'On a schedule, it scrapes, scores, and applies — then writes a tailored letter.' },
  { icon: CheckCircle2, title: 'You review', desc: 'Open the dashboard to see what ran, what matched, and who replied.' },
]

const FEATURES = [
  { icon: Radar, title: 'Auto Scrape', desc: 'Internshala, Naukri & more on a timer — zero manual scrolling.' },
  { icon: FileSearch, title: 'Smart Matching', desc: 'Scores every role against your resumes and auto-picks the best fit.' },
  { icon: PenLine, title: 'AI Cover Letters', desc: 'A local LLM writes a tailored letter for each application.' },
  { icon: Mail, title: 'Response Tracking', desc: 'Reads your inbox and auto-updates pipeline status.' },
  { icon: Gauge, title: 'Live Health Check', desc: 'In-app status checks — no heavy monitoring containers.' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-bg text-ink flex flex-col">
      {/* Top nav */}
      <header className="w-full border-b border-line bg-surface/80 backdrop-saturate-150 sticky top-0 z-20">
        <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand text-white flex items-center justify-center">
              <Compass className="w-[18px] h-[18px]" strokeWidth={2.2} />
            </div>
            <span className="text-[15px] font-bold tracking-tight">JobPilot</span>
          </div>
          <nav className="hidden sm:flex items-center gap-7 text-[13px] font-medium text-ink-soft">
            <a href="#how" className="hover:text-ink transition-colors">How it works</a>
            <a href="#features" className="hover:text-ink transition-colors">Features</a>
          </nav>
          <Link to="/dashboard" className="btn-primary">
            Launch Dashboard <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1">
        <section className="mx-auto max-w-6xl px-6 pt-20 pb-16 md:pt-28 md:pb-20">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 text-xs font-semibold text-brand-strong bg-brand-soft border border-line rounded-md px-2.5 py-1 mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-success" /> Local-first · No cloud · Free
            </div>
            <h1 className="text-4xl md:text-[3.25rem] font-bold tracking-tight leading-[1.1]">
              Your job hunt, on autopilot.
            </h1>
            <p className="mt-5 text-lg text-ink-soft leading-relaxed max-w-xl">
              JobPilot scrapes, scores, and applies to roles on <span className="font-semibold text-ink">your machine</span> —
              then writes a tailored letter and tracks every response. You only open the dashboard to see results.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link to="/dashboard" className="btn-primary text-sm px-5 py-2.5">
                Start Exploring <ArrowRight className="w-4 h-4" />
              </Link>
              <a href="#how" className="text-sm font-semibold text-ink-soft hover:text-ink transition-colors">See how it works</a>
            </div>
          </div>

          {/* Stats strip */}
          <div className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-px bg-line border border-line rounded-xl overflow-hidden">
            {[
              { k: '3', v: 'Job portals' },
              { k: '1', v: 'Local LLM' },
              { k: '0', v: 'Cloud accounts' },
              { k: '100%', v: 'Yours to keep' },
            ].map((s) => (
              <div key={s.v} className="bg-surface px-5 py-4">
                <p className="num text-2xl font-semibold text-ink">{s.k}</p>
                <p className="text-xs font-medium text-ink-soft mt-0.5">{s.v}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section id="how" className="mx-auto max-w-6xl px-6 py-14 border-t border-line">
          <div className="max-w-xl mb-10">
            <h2 className="text-2xl font-bold tracking-tight">How it works</h2>
            <p className="mt-2 text-[15px] text-ink-soft">Three steps. Then it runs itself in the background.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {STEPS.map((s, i) => (
              <div key={s.title} className="card p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-9 h-9 rounded-lg bg-brand-soft text-brand-strong flex items-center justify-center">
                    <s.icon className="w-[18px] h-[18px]" strokeWidth={2} />
                  </div>
                  <span className="num text-xs font-semibold text-ink-faint">0{i + 1}</span>
                </div>
                <h3 className="text-[15px] font-semibold text-ink">{s.title}</h3>
                <p className="mt-1.5 text-[13px] text-ink-soft leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section id="features" className="mx-auto max-w-6xl px-6 py-14 border-t border-line">
          <div className="max-w-xl mb-10">
            <h2 className="text-2xl font-bold tracking-tight">Everything the loop needs</h2>
            <p className="mt-2 text-[15px] text-ink-soft">A complete pipeline that lives on your hardware.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f) => (
              <div key={f.title} className="card p-6 transition-colors hover:border-line-strong">
                <div className="w-10 h-10 rounded-lg bg-brand-soft text-brand-strong flex items-center justify-center mb-4">
                  <f.icon className="w-5 h-5" strokeWidth={2} />
                </div>
                <h3 className="text-[15px] font-semibold text-ink">{f.title}</h3>
                <p className="mt-1.5 text-[13px] text-ink-soft leading-relaxed">{f.desc}</p>
              </div>
            ))}
            {/* CTA card fills the grid */}
            <div className="card p-6 flex flex-col justify-center bg-surface2">
              <p className="text-[15px] font-semibold text-ink">Ready when you are</p>
              <p className="mt-1.5 text-[13px] text-ink-soft leading-relaxed">Spin it up and open the dashboard in a couple of minutes.</p>
              <Link to="/dashboard" className="btn-primary mt-4 self-start">
                Launch Dashboard <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line bg-surface">
        <div className="mx-auto max-w-6xl px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-ink-faint">
          <span className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-brand flex items-center justify-center">
              <Compass className="w-2.5 h-2.5 text-white" />
            </div>
            JobPilot — the loop runs itself. You run the chase.
          </span>
          <span>Self-hosted · MIT</span>
        </div>
      </footer>
    </div>
  )
}
