// src/pages/Home.tsx
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  Activity, MessageSquareText, ShieldCheck, Link2,
  ArrowRight, Database, Eye, CheckCircle2,
  AlertTriangle, Zap, Layers, Search
} from "lucide-react";

const fadeInUp = {
  initial: { opacity: 0, y: 30 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 },
};

const Home = () => (
  <div>
    {/* ═══════ HERO ═══════ */}
    <section className="relative overflow-hidden bg-gradient-to-br from-gray-900 via-primary-900 to-gray-900">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 0)`,
          backgroundSize: '40px 40px',
        }} />
      </div>

      <div className="relative max-w-7xl mx-auto px-6 py-20 md:py-32">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <motion.div {...fadeInUp}>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary-500/20 border border-primary-400/30 rounded-full mb-6">
              <Zap className="w-3.5 h-3.5 text-primary-400" />
              <span className="text-xs font-semibold text-primary-300">Track 1 — Hackathon 2026</span>
            </div>

            <h1 className="text-4xl md:text-6xl font-extrabold text-white leading-tight">
              Hospital Data,<br />
              <span className="bg-gradient-to-r from-primary-400 to-source-500 bg-clip-text text-transparent">
                Finally Clear
              </span>
            </h1>

            <p className="mt-6 text-lg text-gray-300 max-w-lg leading-relaxed">
              Reconstruct patient timelines from fragmented hospital tables.
              Ask questions in plain English. Every answer links back to its
              <span className="text-source-500 font-semibold"> source row</span>.
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                to="/timeline"
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-500 text-white rounded-xl font-semibold shadow-lg shadow-primary-600/30 transition-all"
              >
                <Activity className="w-5 h-5" />
                Explore Timeline
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/query"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-xl font-semibold transition-all"
              >
                <MessageSquareText className="w-5 h-5" />
                Ask a Question
              </Link>
            </div>
          </motion.div>

          <motion.div
            {...fadeInUp}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="hidden md:block"
          >
            <div className="relative bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center justify-between gap-3 mb-4">
                <div className="flex-1 bg-source-500/20 border border-source-500/40 rounded-xl p-3 text-center">
                  <Database className="w-6 h-6 text-source-400 mx-auto mb-1" />
                  <p className="text-[10px] text-source-300 font-semibold">10+ Tables</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-500 shrink-0" />
                <div className="flex-1 bg-primary-500/20 border border-primary-500/40 rounded-xl p-3 text-center">
                  <Layers className="w-6 h-6 text-primary-400 mx-auto mb-1" />
                  <p className="text-[10px] text-primary-300 font-semibold">Timeline</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-500 shrink-0" />
                <div className="flex-1 bg-medical-500/20 border border-medical-500/40 rounded-xl p-3 text-center">
                  <CheckCircle2 className="w-6 h-6 text-medical-400 mx-auto mb-1" />
                  <p className="text-[10px] text-medical-300 font-semibold">Verified</p>
                </div>
              </div>
              <div className="space-y-2">
                {[
                  { time: "10:00", icon: "🏥", text: "Admission (Emergency)", color: "bg-primary-500" },
                  { time: "10:15", icon: "🔬", text: "Potassium: 5.2 mEq/L", color: "bg-medical-500" },
                  { time: "10:30", icon: "💊", text: "Metoprolol 25mg PO", color: "bg-warning-500" },
                  { time: "11:00", icon: "🚑", text: "ICU Admission — MICU", color: "bg-danger-500" },
                  { time: "11:05", icon: "📊", text: "Heart Rate: 92 bpm", color: "bg-source-500" },
                  { time: "12:00", icon: "🔬", text: "Creatinine: 1.4 ⚠️", color: "bg-danger-500" },
                ].map((e, i) => (
                  <div key={i} className="flex items-center gap-3 bg-white/5 rounded-lg px-3 py-2">
                    <span className="text-[10px] text-gray-400 w-10 font-mono">{e.time}</span>
                    <div className={`w-2 h-2 rounded-full ${e.color}`} />
                    <span className="text-xs text-gray-300">{e.icon} {e.text}</span>
                    <span className="ml-auto text-[9px] text-source-400 font-mono">🔗 source</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>

    {/* ═══════ WHAT IS THIS ═══════ */}
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div {...fadeInUp} className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900">What is this project?</h2>
          <div className="mt-4 w-20 h-1 bg-primary-500 mx-auto rounded-full" />
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: Database, color: "source",
              title: "Fragmented Data",
              desc: "A single patient admission spans 10+ relational tables — labs, meds, diagnoses, ICU observations. Each has different keys and timestamps.",
              visual: "📋 admissions\n🔬 labevents (107K)\n💊 prescriptions (18K)\n🩺 chartevents (668K)\n🏥 icustays (140)"
            },
            {
              icon: AlertTriangle, color: "warning",
              title: "The Problem",
              desc: "Before hospital data can support research, teams must manually reconstruct context, check quality, prevent leakage, and trace every claim. This takes hours.",
              visual: "❌ No unified view\n❌ No source tracing\n❌ No quality checks\n❌ No leakage detection\n❌ Manual SQL queries"
            },
            {
              icon: Activity, color: "primary",
              title: "Our Solution",
              desc: "A tool that reconstructs patient timelines, answers questions with verified evidence, validates data quality, and traces every claim to its source row.",
              visual: "✅ Time-ordered timeline\n✅ Smart query engine\n✅ Source trace on every event\n✅ Verification gate\n✅ Quality & leakage checks"
            },
          ].map((card, i) => (
            <motion.div key={i} {...fadeInUp} transition={{ delay: i * 0.15, duration: 0.6 }}
              className="bg-gray-50 border border-gray-200 rounded-2xl p-6 hover:shadow-lg hover:border-gray-300 transition-all">
              <div className={`w-12 h-12 rounded-xl bg-${card.color}-100 flex items-center justify-center mb-4`}>
                <card.icon className={`w-6 h-6 text-${card.color}-600`} />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">{card.title}</h3>
              <p className="text-sm text-gray-600 leading-relaxed mb-4">{card.desc}</p>
              <pre className="text-xs bg-gray-100 rounded-lg p-3 text-gray-700 font-mono leading-relaxed whitespace-pre-wrap">{card.visual}</pre>
            </motion.div>
          ))}
        </div>
      </div>
    </section>

    {/* ═══════ HOW IT WORKS ═══════ */}
    <section className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div {...fadeInUp} className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900">How it works</h2>
          <div className="mt-4 w-20 h-1 bg-medical-500 mx-auto rounded-full" />
          <p className="mt-4 text-gray-600 max-w-2xl mx-auto">
            Pattern matching translates your question to a database query. We execute it. We verify the results. Zero rows = no answer.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-5 gap-4">
          {[
            { step: 1, icon: MessageSquareText, title: "You ask", desc: "Natural language question", color: "primary" },
            { step: 2, icon: Search, title: "Match", desc: "Pattern → query rule", color: "medical" },
            { step: 3, icon: Database, title: "Execute", desc: "Run query on MongoDB", color: "source" },
            { step: 4, icon: CheckCircle2, title: "Verify", desc: "Rows > 0? → Answer", color: "medical" },
            { step: 5, icon: Link2, title: "Evidence", desc: "Source trace attached", color: "warning" },
          ].map((s, i) => {
            const Icon = s.icon;
            return (
              <motion.div key={i} {...fadeInUp} transition={{ delay: i * 0.1, duration: 0.5 }} className="text-center">
                <div className={`w-14 h-14 mx-auto rounded-2xl bg-${s.color}-100 border-2 border-${s.color}-300 flex items-center justify-center mb-3 shadow-lg`}>
                  <Icon className={`w-7 h-7 text-${s.color}-600`} />
                </div>
                <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                  <span className={`inline-block px-2 py-0.5 bg-${s.color}-100 text-${s.color}-700 rounded text-[10px] font-bold mb-2`}>STEP {s.step}</span>
                  <h4 className="font-bold text-gray-900 text-sm">{s.title}</h4>
                  <p className="text-xs text-gray-500 mt-1">{s.desc}</p>
                </div>
              </motion.div>
            );
          })}
        </div>

        <motion.div {...fadeInUp} className="mt-12 bg-gradient-to-r from-medical-50 to-source-50 border-2 border-medical-500/30 rounded-2xl p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-medical-500 flex items-center justify-center shrink-0">
              <Eye className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Verification Gate — No Hallucination</h3>
              <p className="text-sm text-gray-600 mt-2 leading-relaxed">
                The system <strong>refuses to answer</strong> when zero supporting rows are found.
                It cannot fabricate data. If the data doesn't exist in MIMIC-IV, it says: <em>"No supporting data found."</em>
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>

    {/* ═══════ 4 MODULES ═══════ */}
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div {...fadeInUp} className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900">Four Powerful Modules</h2>
          <div className="mt-4 w-20 h-1 bg-medical-500 mx-auto rounded-full" />
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8">
          {[
            {
              path: "/timeline", icon: Activity, color: "primary", gradient: "from-primary-500 to-primary-700",
              title: "Patient Timeline", subtitle: "Reconstruct the=the complete patient journey",
              features: ["Time-ordered events from 10+ tables", "Admissions, labs, meds, diagnoses, ICU data", "Source trace on every single event", "High-volume event grouping", "Abnormal flags & uncertainty indicators"],
            },
            {
              path: "/query", icon: MessageSquareText, color: "medical", gradient: "from-medical-500 to-medical-700",
              title: "Smart Query", subtitle: "Ask questions with verified answers",
              features: ["Pattern matching → MongoDB query", "20+ built-in question patterns", "Verification gate: 0 rows = no answer", "Every answer includes source evidence", "No API calls needed"],
            },
            {
              path: "/validation", icon: ShieldCheck, color: "warning", gradient: "from-warning-500 to-warning-700",
              title: "Data Validation", subtitle: "Quality checks & leakage detection",
              features: ["Temporal consistency checks", "Missing timestamp detection", "Implausible value detection", "Patient-level leakage detection", "Temporal leakage detection"],
            },
            {
              path: "/evidence", icon: Link2, color: "source", gradient: "from-source-500 to-source-700",
              title: "Evidence Trace", subtitle: "Navigate from any claim to its source document",
              features: ["Every event links to source collection + doc_id", "Click to view raw source document", "Batch verification of source traces", "Source provenance coverage metrics", "AI vs Source visual distinction"],
            },
          ].map((mod, i) => (
            <motion.div key={i} {...fadeInUp} transition={{ delay: i * 0.1, duration: 0.6 }}>
              <Link to={mod.path} className="block bg-gray-50 border border-gray-200 rounded-2xl overflow-hidden hover:shadow-xl hover:border-gray-300 transition-all group">
                <div className={`bg-gradient-to-r ${mod.gradient} px-6 py-4`}>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                      <mod.icon className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white">{mod.title}</h3>
                      <p className="text-sm text-white/80">{mod.subtitle}</p>
                    </div>
                    <ArrowRight className="w-5 h-5 text-white/60 ml-auto group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
                <div className="p-6">
                  <ul className="space-y-2">
                    {mod.features.map((f, fi) => (
                      <li key={fi} className="flex items-start gap-2 text-sm text-gray-700">
                        <CheckCircle2 className={`w-4 h-4 text-${mod.color}-500 shrink-0 mt-0.5`} />
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>

    {/* ═══════ DATASET ═══════ */}
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <motion.div {...fadeInUp} className="bg-gray-50 border border-gray-200 rounded-2xl p-8">
          <div className="flex items-start gap-6">
            <div className="w-14 h-14 bg-primary-100 rounded-xl flex items-center justify-center shrink-0">
              <Database className="w-7 h-7 text-primary-600" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">Dataset: MIMIC-IV Demo v2.2</h3>
              <p className="text-sm text-gray-600 mt-2 leading-relaxed">
                100"100 patients from one tertiary academic medical center in Boston, USA.
                Retrospective, deidentified data with date shifting. No free-text clinical notes.
                This is an educational sample — <strong>not sufficient</strong> for clinical validity claims.
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                {[
                  { label: "Patients", value: "100" },
                  { label: "Admissions", value: "275" },
                  { label: "Lab Events", value: "107,727" },
                  { label: "Chart Events", value: "668,862" },
                  { label: "Prescriptions", value: "18,087" },
                  { label: "ICU Stays", value: "140" },
                ].map((s) => (
                  <div key={s.label} className="bg-white border border-gray-200 rounded-lg px-3 py-2 text-center">
                    <p className="text-lg font-bold text-primary-600">{s.value}</p>
                    <p className="text-[10px] text-gray-500">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  </div>
);

export default Home;