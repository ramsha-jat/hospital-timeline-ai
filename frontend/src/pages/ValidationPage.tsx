// src/pages/ValidationPage.tsx
import { useState, useEffect } from "react";
import { ShieldCheck, CheckCircle2, AlertTriangle, Database } from "lucide-react";

const API = "https://hospital-timeline-ai-production.up.railway.app/api";

const ValidationPage = () => {
  const [inputId, setInputId] = useState("");
  const [quality, setQuality] = useState<any>(null);
  const [census, setCensus] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/validation/census`).then(r => r.json()).then(setCensus).catch(() => {});
  }, []);

  const checkQuality = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/validation/quality/${inputId}`);
      setQuality(await res.json());
    } catch {}
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <div className="w-10 h-10 bg-medical-100 rounded-xl flex items-center justify-center">
            <ShieldCheck className="w-5 h-5 text-medical-600" />
          </div>
          Data Validation
        </h1>
        <p className="text-gray-600 mt-2">Quality checks & leakage detection for research credibility</p>
      </div>

      {/* Census */}
      {census && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-source-500" /> Dataset Census
          </h3>
          <div className="grid grid-cols-3 sm:grid-cols-5 gap-3">
            {Object.entries(census.table_counts || {}).map(([name, count]: any) => (
              <div key={name} className="bg-gray-50 border border-gray-200 rounded-lg p-2.5 text-center">
                <p className="text-lg font-bold text-primary-600">{(count as number).toLocaleString()}</p>
                <p className="text-[10px] text-gray-500 truncate">{name}</p>
              </div>
            ))}
          </div>
          <div className="mt-3 flex gap-4 text-xs text-gray-500">
            <span>Total patients: <strong>{census.total_patients}</strong></span>
            <span>Total admissions: <strong>{census.total_admissions}</strong></span>
          </div>
        </div>
      )}

      {/* Quality check input */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 shadow-sm">
        <h3 className="font-bold text-gray-900 mb-3">Quality Check for Admission</h3>
        <div className="flex gap-2">
          <input
            type="number"
            value={inputId}
            onChange={(e) => setInputId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && checkQuality()}
            placeholder="hadm_id"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
          <button onClick={checkQuality} disabled={loading} className="px-5 py-2 bg-medical-600 hover:bg-medical-500 text-white rounded-lg text-sm font-medium disabled:opacity-50">
            {loading ? "..." : "Check"}
          </button>
        </div>
      </div>

      {/* Quality result */}
      {quality && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            {quality.valid ? (
              <CheckCircle2 className="w-8 h-8 text-medical-600" />
            ) : (
              <AlertTriangle className="w-8 h-8 text-danger-600" />
            )}
            <div>
              <h3 className="font-bold text-gray-900">
                {quality.valid ? "Data Quality: PASS" : "Data Quality: ISSUES FOUND"}
              </h3>
              <p className="text-xs text-gray-500">hadm_id: {quality.hadm_id}</p>
            </div>
          </div>

          {quality.issues?.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-bold text-danger-600 uppercase mb-2">Issues</h4>
              {quality.issues.map((issue: string, i: number) => (
                <div key={i} className="flex items-center gap-2 text-sm text-danger-700 mb-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-danger-500" />
                  {issue}
                </div>
              ))}
            </div>
          )}

          {quality.warnings?.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-bold text-warning-600 uppercase mb-2">Warnings</h4>
              {quality.warnings.map((w: string, i: number) => (
                <div key={i} className="flex items-center gap-2 text-sm text-warning-700 mb-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-warning-500" />
                  {w}
                </div>
              ))}
            </div>
          )}

          {quality.valid && quality.issues?.length === 0 && (
            <p className="text-sm text-medical-600">✅ No issues detected for this admission.</p>
          )}

          <p className="text-[10px] text-gray-400 mt-4 italic">{quality.disclaimer}</p>
        </div>
      )}
    </div>
  );
};

export default ValidationPage;
