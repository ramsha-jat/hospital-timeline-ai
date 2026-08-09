// src/pages/QueryPage.tsx
import { useState } from "react";
import { motion } from "framer-motion";
import {
  MessageSquareText, Send, Database,
  AlertTriangle, CheckCircle2, ChevronDown, ChevronRight,
  Pill, TestTube2, Stethoscope, Activity, ArrowRightLeft,
  BedDouble, FlaskConical, Heart, Wind, Droplets, Search
} from "lucide-react";

const API = "https://hospital-timeline-ai-production.up.railway.app/api";

const CATEGORY_ICONS: Record<string, any> = {
  medications: Pill, abnormal_labs: TestTube2, all_labs: TestTube2,
  diagnoses: Stethoscope, procedures: Activity, icu_stay: BedDouble,
  transfers: ArrowRightLeft, potassium: FlaskConical, creatinine: FlaskConical,
  glucose: FlaskConical, hemoglobin: FlaskConical, wbc: FlaskConical,
  lactate: FlaskConical, heart_rate: Heart, bp_chart: Activity,
  spo2: Wind, outputs: Droplets,
};

const QueryPage = () => {
  const [hadmId, setHadmId] = useState("24181354");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [showEvidence, setShowEvidence] = useState(false);
  const [showQuery, setShowQuery] = useState(false);

  const ask = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API}/query/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, hadm_id: parseInt(hadmId) }),
      });
      const data = await res.json();
      setResult(data);
      setHistory((prev) => [{ question, ...data }, ...prev].slice(0, 10));
      setQuestion("");
    } catch (e: any) {
      setResult({ error: e.message, refused: true });
    } finally {
      setLoading(false);
    }
  };

  const ruleId = result?.query?.rule_id || "";
  const CategoryIcon = CATEGORY_ICONS[ruleId] || Search;

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <div className="w-10 h-10 bg-medical-100 rounded-xl flex items-center justify-center">
            <MessageSquareText className="w-5 h-5 text-medical-600" />
          </div>
          Smart Query
        </h1>
        <p className="text-gray-600 mt-2">Ask questions about structured clinical data — answers verified against source rows</p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-200 p-5 mb-6 shadow-sm">
        <div className="mb-3">
          <label className="text-xs font-semibold text-gray-500 uppercase">Admission ID</label>
          <input type="number" value={hadmId} onChange={(e) => setHadmId(e.target.value)}
            className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none" />
        </div>
        <div className="flex gap-2">
          <input type="text" value={question} onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
            placeholder="e.g., What lab tests were abnormal?"
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
            disabled={loading} />
          <button onClick={ask} disabled={loading || !question.trim()}
            className="px-5 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium text-sm disabled:opacity-50 flex items-center gap-2 transition-colors">
            <Send className="w-4 h-4" />
            {loading ? "..." : "Ask"}
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {["What lab tests were abnormal?", "What medications were prescribed?", "What were the diagnoses?",
            "How long was the ICU stay?", "Potassium levels?", "Heart rate observations?", "Blood pressure readings?"].map((s) => (
            <button key={s} onClick={() => setQuestion(s)}
              className="text-xs bg-gray-100 hover:bg-primary-50 hover:text-primary-700 text-gray-600 px-3 py-1.5 rounded-lg transition-colors">{s}</button>
          ))}
        </div>
      </div>

      {result && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          {result.refused ? (
            <div className="bg-warning-50 border-2 border-warning-200 rounded-2xl p-5">
              <div className="flex items-center gap-3 mb-2">
                <AlertTriangle className="w-6 h-6 text-warning-600" />
                <h3 className="font-bold text-warning-800">No Data Found</h3>
              </div>
              <p className="text-sm text-warning-700 leading-relaxed">{result.answer || result.error || "No supporting data found for this query."}</p>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-3 bg-gray-50 border-b border-gray-100 flex items-center gap-3 flex-wrap">
                <CategoryIcon className="w-4 h-4 text-primary-600" />
                <span className="text-xs font-semibold text-gray-700">{ruleId.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase())}</span>
                <span className="px-2 py-0.5 bg-medical-100 text-medical-700 rounded text-[10px] font-bold">⚡ Rule-based</span>
                <div className="flex items-center gap-1.5 ml-auto">
                  <CheckCircle2 className="w-4 h-4 text-medical-500" />
                  <span className="text-xs font-medium text-medical-700">{result.supporting_rows} source rows</span>
                </div>
              </div>

              <div className="p-5">
                {result.answer && (
                  <div className="space-y-2 text-sm text-gray-800 leading-relaxed whitespace-pre-wrap font-mono">
                    {result.answer}
                  </div>
                )}
              </div>

              <div className="border-t border-gray-100 px-5 py-3 flex gap-4">
                <button onClick={() => setShowEvidence(!showEvidence)}
                  className="flex items-center gap-2 text-xs font-medium text-source-600 hover:text-source-700">
                  <Database className="w-3.5 h-3.5" />
                  {showEvidence ? "Hide" : "Show"} Evidence ({result.evidence?.length || 0})
                  {showEvidence ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                </button>
                <button onClick={() => setShowQuery(!showQuery)}
                  className="flex items-center gap-2 text-xs font-medium text-gray-500 hover:text-gray-700">
                  {showQuery ? "Hide" : "Show"} Query
                </button>
              </div>

              {showEvidence && result.evidence?.length > 0 && (
                <div className="border-t border-gray-100 p-5">
                  <div className="overflow-x-auto max-h-64 overflow-y-auto rounded-lg border border-gray-200">
                    <table className="text-xs w-full">
                      <thead className="bg-source-50 sticky top-0">
                        <tr>
                          {Object.keys(result.evidence[0].data).slice(0, 5).map((k) => (
                            <th key={k} className="px-2 py-2 text-left text-source-700 font-semibold">{k}</th>
                          ))}
                          <th className="px-2 py-2 text-left text-source-700 font-semibold">Source</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.evidence.slice(0, 30).map((row: any, i: number) => (
                          <tr key={i} className="border-t border-gray-100 hover:bg-source-50/30">
                            {Object.values(row.data).slice(0, 5).map((v: any, j: number) => (
                              <td key={j} className="px-2 py-1.5 text-gray-700 max-w-[120px] truncate">
                                {v === null ? <span className="italic text-gray-300">null</span> : String(v).substring(0, 30)}
                              </td>
                            ))}
                            <td className="px-2 py-1.5">
                              <span className="text-[9px] font-mono text-source-600 bg-source-50 px-1.5 py-0.5 rounded">
                                {row.source_trace.collection}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {showQuery && (
                <div className="border-t border-gray-100 p-5">
                  <pre className="text-xs bg-gray-50 rounded-lg p-3 overflow-x-auto font-mono text-gray-700">
                    {JSON.stringify(result.query, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}

      {history.length > 0 && (
        <div className="mt-8">
          <h3 className="text-sm font-semibold text-gray-500 mb-3">Recent Questions</h3>
          <div className="space-y-2">
            {history.map((h, i) => (
              <div key={i} className="border-l-2 border-gray-200 pl-3 py-1.5">
                <p className="text-sm text-gray-600">"{h.question}"</p>
                <span className={`text-[10px] ${h.refused ? "text-warning-500" : "text-medical-500"}`}>
                  {h.refused ? "❌ no data" : `✅ ${h.supporting_rows} rows`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default QueryPage;
