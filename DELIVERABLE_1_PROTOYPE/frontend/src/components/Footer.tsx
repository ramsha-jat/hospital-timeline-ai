// src/components/Footer.tsx
const Footer = () => (
  <>
    {/* FIXED SAFETY BANNER — challenge requirement */}
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-r from-danger-600 to-danger-500 text-white text-center py-2 shadow-[0_-4px_20px_rgba(239,68,68,0.3)]">
      <p className="text-xs font-bold tracking-wide">
        ⚠️ Research & educational prototype only — NOT for clinical use. Do not use for diagnosis, treatment, triage, or emergency decisions.
      </p>
    </div>

    {/* Actual footer */}
    <footer className="bg-gray-900 text-gray-400 pb-10">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-white font-bold mb-2">Hospital Timeline AI</h3>
            <p className="text-sm">Track 1 — Structured Patient Timeline & Evidence Retrieval</p>
            <p className="text-xs mt-2">MIMIC-IV Clinical Database Demo v2.2</p>
          </div>
          <div>
            <h4 className="text-white font-semibold text-sm mb-2">Citation</h4>
            <p className="text-xs">Johnson et al. (2023). MIMIC-IV Clinical Database Demo (v2.2). PhysioNet.</p>
          </div>
          <div>
            <h4 className="text-white font-semibold text-sm mb-2">Stack</h4>
            <p className="text-xs">React + FastAPI + MongoDB + Gemini AI</p>
          </div>
        </div>
      </div>
    </footer>
  </>
);

export default Footer;