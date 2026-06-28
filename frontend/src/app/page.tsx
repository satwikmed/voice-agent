"use client"
import Link from "next/link"
import { motion } from "framer-motion"
import { MeshGradient, PulsingBorder } from "@paper-design/shaders-react"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden font-sans pb-20">
      {/* Dynamic Background Mesh */}
      <div className="absolute inset-0 w-full h-full pointer-events-none">
        <MeshGradient
          className="w-full h-full opacity-55"
          colors={["#000000", "#06b6d4", "#0891b2", "#164e63", "#f97316"]}
          speed={0.15}
        />
      </div>

      {/* Floating Sparkles decorative element */}
      <div className="absolute top-20 left-10 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none animate-pulse"></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl pointer-events-none animate-pulse"></div>

      <header className="relative z-20 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full flex items-center justify-center bg-cyan-500/20 border border-cyan-500/40">
            <span className="text-cyan-400 font-black text-base">V</span>
          </div>
          <span className="text-lg font-black tracking-wider uppercase bg-gradient-to-r from-cyan-400 to-white bg-clip-text text-transparent">
            VoiceIQ
          </span>
        </div>
        <Link 
          href="/portal"
          className="px-5 py-2 rounded-full border border-white/20 bg-white/5 hover:bg-white/10 text-xs font-semibold uppercase tracking-wider transition duration-300 backdrop-blur-md"
        >
          Launch App
        </Link>
      </header>

      <main className="relative z-10 max-w-5xl mx-auto px-8 mt-16 text-center space-y-16">
        
        {/* Hero Banner Section */}
        <section className="space-y-6">
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] text-cyan-400 uppercase tracking-widest font-bold backdrop-blur-sm"
          >
            <span>✨</span> Built for Retell AI voice agents
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-7xl font-extrabold tracking-tight leading-none"
          >
            How do you test a <br/>
            <span className="bg-gradient-to-r from-cyan-400 via-white to-orange-400 bg-clip-text text-transparent">
              Robot Phone Call?
            </span>
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-base md:text-lg text-white/60 max-w-2xl mx-auto leading-relaxed"
          >
            VoiceIQ tests Retell voice agents <em>before</em> they go live — scripted
            caller personas, LLM-as-judge scoring, and a deploy gate. Retell Assure
            covers post-launch. Together that&apos;s the full quality loop.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="pt-6 flex justify-center gap-4"
          >
            <Link
              href="/portal"
              className="px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-orange-500 text-white font-bold text-xs uppercase tracking-widest transition duration-300 hover:shadow-lg hover:shadow-cyan-500/20 transform hover:-translate-y-0.5"
            >
              🚀 Launch Simulator App
            </Link>
          </motion.div>
        </section>

        {/* Retell lifecycle */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold tracking-tight text-white/90">Before launch + after launch</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-cyan-500/20 bg-white/5 p-6 text-left backdrop-blur-md">
              <p className="label-muted mb-2 text-[10px] uppercase tracking-widest text-cyan-400">Pre-production · VoiceIQ</p>
              <p className="text-xs leading-relaxed text-white/50">
                Scenario suites, coverage heatmaps, Retell prompt import, and a deploy gate — ship only when your agent passes.
              </p>
            </div>
            <div className="rounded-2xl border border-orange-500/20 bg-white/5 p-6 text-left backdrop-blur-md">
              <p className="mb-2 text-[10px] uppercase tracking-widest text-orange-400">Post-production · Retell Assure</p>
              <p className="text-xs leading-relaxed text-white/50">
                Retell&apos;s own QA layer monitors live calls. VoiceIQ is the missing pre-launch half of that story.
              </p>
            </div>
          </div>
        </section>

        {/* Explain the Flow (Steps) */}
        <section className="space-y-12">
          <h2 className="text-2xl font-bold tracking-tight text-white/90">How it Works, Step-by-Step</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Step 1 */}
            <div className="p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md text-left space-y-3 relative group hover:border-cyan-500/30 transition duration-300">
              <div className="w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-xs font-black text-cyan-400">1</div>
              <h3 className="font-bold text-base">The Mock Call</h3>
              <p className="text-xs text-white/50 leading-relaxed">
                We load up two AI systems. One plays the role of your **AI Support Bot**. The other plays a **Mock Customer** (like an angry customer trying to cancel, or a confused buyer asking questions). They talk to each other just like a real phone call.
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md text-left space-y-3 relative group hover:border-orange-500/30 transition duration-300">
              <div className="w-8 h-8 rounded-full bg-orange-500/10 border border-orange-500/30 flex items-center justify-center text-xs font-black text-orange-400">2</div>
              <h3 className="font-bold text-base">The AI Judge Grades</h3>
              <p className="text-xs text-white/50 leading-relaxed">
                An objective **AI Referee** reads the entire typed conversation. It looks at key dimensions like *objection handling*, *empathy*, and whether the customer got what they wanted. It then awards a grade out of 100.
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md text-left space-y-3 relative group hover:border-white/20 transition duration-300">
              <div className="w-8 h-8 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-xs font-black text-white">3</div>
              <h3 className="font-bold text-base">Verification (Calibration)</h3>
              <p className="text-xs text-white/50 leading-relaxed">
                To make sure the AI Referee isn't just grading randomly, we compare its scores with **real human evaluations**. The closer the AI grades are to the human grades, the more we can trust it to test our product.
              </p>
            </div>

          </div>
        </section>

        {/* Visual Mock Call Demo Section */}
        <section className="p-8 rounded-3xl border border-white/10 bg-black/40 backdrop-blur-md relative overflow-hidden flex flex-col md:flex-row items-center gap-8 text-left">
          <div className="absolute top-4 right-4">
            <PulsingBorder
              colors={["#06b6d4", "#f97316"]}
              colorBack="#00000000"
              speed={1.5}
              roundness={1}
              thickness={0.08}
              intensity={4}
              spots={3}
              style={{ width: "45px", height: "45px" }}
            />
          </div>
          <div className="flex-1 space-y-4">
            <h3 className="text-xl font-bold tracking-tight">Try it in Action</h3>
            <p className="text-xs text-white/60 leading-relaxed max-w-md">
              In our live simulator tab, you can input your own prompt configurations, choose a custom scenario, click **Simulate**, and watch the AI systems execute the conversation loop live in front of you.
            </p>
            <div className="pt-2">
              <Link
                href="/portal"
                className="inline-flex items-center gap-1.5 text-xs text-cyan-400 font-bold uppercase tracking-wider group hover:text-cyan-300 transition"
              >
                Go to Simulator Tab <span className="group-hover:translate-x-1 transition duration-150">→</span>
              </Link>
            </div>
          </div>
          <div className="w-full md:w-80 p-4 rounded-xl bg-white/5 border border-white/5 space-y-3 font-mono text-[10px] text-white/40">
            <div className="p-2.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-300">
              🤖 <strong>AI Agent:</strong> Hi, thanks for calling. How can I help?
            </div>
            <div className="p-2.5 rounded bg-orange-500/10 border border-orange-500/20 text-orange-300">
              📞 <strong>Angry Customer:</strong> I want to cancel my account. It is too slow!
            </div>
            <div className="p-2.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-300">
              🤖 <strong>AI Agent:</strong> I can process that refund immediately...
            </div>
            <div className="text-center text-[9px] text-white/20 pt-1 font-semibold uppercase tracking-wider">
              ✨ 3x Consistency Check Active
            </div>
          </div>
        </section>

      </main>

      <footer className="mt-20 border-t border-white/5 pt-8 text-center text-[10px] text-white/30 uppercase tracking-widest relative z-20">
        VoiceIQ © 2026 · Built for Retell AI · Not affiliated with Retell
      </footer>
    </div>
  )
}
