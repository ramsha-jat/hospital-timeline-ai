// src/pages/EvidencePage.tsx
import { useState } from "react";
import { Link2, Database } from "lucide-react";

const API = "/api";

const EvidencePage = () => {
  const [collection, setCollection] = useState("labevents");
  const [docId, setDocId] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);

  const collections = [
    "patients", "admissions", "icustays", "transfers",
    "labevents", "prescriptions", "diagnoses_icd", "procedures_icd",
    "chartevents", "outputevents", "d_labitems", "d_items",
  ];

  const lookup = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/evidence/trace/${collection}/${docId}`);
      setResult(await res.json());
    } catch (e: any) {
      setResult({ error: e.message });
    }
    setLoading(false);
  };

  const loadStats = async () => {
    try {
      const res = await fetch(`${API}/evidence/collection-stats`);
      setStats(await res.json());
    } catch {}
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <div className="w-10 h-10 bg-source-100 rounded-xl flex items-center justify-center">
            <Link2 className="w-5 h-5 text-source-600" />
          </div>
          Evidence Trace
        </h1>
        <p className="text-gray-600 mt-2">Navigate from any claim back to its source MongoDB document</p>
      </div>

      {/* Lookup */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 shadow-sm">
        <h3 className="font-bold text-gray-900 mb-3">Source Document Lookup</h3>
        <div className="flex gap-2 mb-3">
          <select
            value={collection}
            onChange={(e) => setCollection(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
          >
            {collections.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <input
            type="text"
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && lookup()}
            placeholder="Document ID"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
          <button onClick={lookup} disabled={loading} className="px-5 py-2 bg-source-600 hover:bg-source-500 text-white rounded-lg text-sm font-medium disabled:opacity-50">
            {loading ? "..." : "Lookup"}
          </button>
        </div>
      </div>

      {/* Result */}
      {result && !result.error && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="border-l-4 border-source-400 bg-source-50/30 px-5 py-3">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-source-500" />
              <span className="text-sm font-bold text-source-700">{result.collection}</span>
              <span className="text-xs text-gray-400">· {result.doc_id}</span>
              <span className="ml-auto text-[9px] bg-source-200 text-source-800 px-1.5 rounded font-bold">SOURCE</span>
            </div>
          </div>
          <div className="p-5">
            <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Raw Document</h4>
            <pre className="text-xs bg-gray-50 rounded-lg p-4 overflow-x-auto max-h-96 overflow-y-auto font-mono text-gray-700 leading-relaxed">
              {JSON.stringify(result.formatted || result.document, null, 2)}
            </pre>
            {result.disclaimer && (
              <p className="text-[10px] text-warning-600 mt-3 italic">⚠️ {result.disclaimer}</p>
            )}
          </div>
        </div>
      )}

      {result?.error && (
        <div className="bg-danger-50 border border-danger-200 rounded-xl p-4">
          <p className="text-sm text-danger-700">❌ {result.error}</p>
        </div>
      )}

      {/* Collection Stats */}
      <div className="mt-8">
        <button onClick={loadStats} className="text-sm text-source-600 hover:underline font-medium">
          Load Collection Stats →
        </button>
        {stats && (
          <div className="mt-4 grid grid-cols-3 sm:grid-cols-5 gap-3">
            {Object.entries(stats.collections || {}).map(([name, info]: any) => (
              <div key={name} className="bg-white border border-gray-200 rounded-lg p-2.5 text-center">
                <p className="text-sm font-bold text-source-600">{(info.document_count as number).toLocaleString()}</p>
                <p className="text-[10px] text-gray-500 truncate">{name}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default EvidencePage;