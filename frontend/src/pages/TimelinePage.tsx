// src/pages/TimelinePage.tsx
import { useState } from "react";
import { motion } from "framer-motion";
import {
  Activity, Search, ChevronDown, ChevronRight, Database
} from "lucide-react";

const API = "/api";

const CATEGORY_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  admission:      { icon: "🏥", color: "text-primary-600",  bg: "bg-primary-100"  },
  discharge:      { icon: "🚪", color: "text-gray-600",     bg: "bg-gray-100"     },
  transfer:       { icon: "↔️", color: "text-primary-600",  bg: "bg-primary-50"   },
  icu_admission:  { icon: "🚑", color: "text-danger-600",   bg: "bg-danger-50"    },
  icu_discharge:  { icon: "🚑", color: "text-danger-500",   bg: "bg-danger-50"    },
  lab_result:     { icon: "🔬", color: "text-medical-600",  bg: "bg-medical-50"   },
  medication:     { icon: "💊", color: "text-warning-600",  bg: "bg-warning-50"   },
  diagnosis:      { icon: "📋", color: "text-ai-600",       bg: "bg-ai-50"        },
  procedure:      { icon: "🔧", color: "text-source-600",   bg: "bg-source-50"    },
  icu_observation:{ icon: "📊", color: "text-source-600",   bg: "bg-source-50"    },
  icu_output:     { icon: "📈", color: "text-source-500",   bg: "bg-source-50"    },
};

const TimelinePage = () => {
  const [inputId, setInputId] = useState("");
  const [timeline, setTimeline] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<any>(null);
  const [filterCat, setFilterCat] = useState<string>("all");
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const loadTimeline = async () => {
    const id = parseInt(inputId);
    if (isNaN(id)) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/timeline/${id}`);
      if (!res.ok) throw new Error(await res.text());
      setTimeline(await res.json());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const events = timeline?.events || [];
  const groups = timeline?.groups || [];
  const filteredEvents = filterCat === "all" ? events : events.filter((e: any) => e.category === filterCat);
  const categories: string[] = [...new Set(events.map((e: any) => e.category))] as string[];

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center">
            <Activity className="w-5 h-5 text-primary-600" />
          </div>
          Patient Timeline
        </h1>
        <p className="text-gray-600 mt-2">Reconstruct the complete patient journey from fragmented hospital tables</p>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 shadow-sm">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="number"
              value={inputId}
              onChange={(e) => setInputId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadTimeline()}
              placeholder="Enter hadm_id (e.g., 20000049)"
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
          <button
            onClick={loadTimeline}
            disabled={loading}
            className="px-6 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium text-sm disabled:opacity-50 transition-colors"
          >
            {loading ? "Loading..." : "Build Timeline"}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-danger-50 border border-danger-200 rounded-xl p-4 mb-6">
          <p className="text-sm text-danger-700">❌ {error}</p>
        </div>
      )}

      {timeline && (
        <>
          {/* Admission info */}
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 shadow-sm">
            <div className="flex flex-wrap items-center gap-6">
              <div>
                <span className="text-xs text-gray-500">Subject</span>
                <p className="text-lg font-bold text-gray-900">{timeline.subject_id}</p>
              </div>
              <div>
                <span className="text-xs text-gray-500">Admission</span>
                <p className="text-lg font-bold text-primary-600">{timeline.hadm_id}</p>
              </div>
              <div>
                <span className="text-xs text-gray-500">Admitted</span>
                <p className="text-sm font-medium text-gray-900">{new Date(timeline.admission_time).toLocaleString()}</p>
              </div>
              {timeline.discharge_time && (
                <div>
                  <span className="text-xs text-gray-500">Discharged</span>
                  <p className="text-sm font-medium text-gray-900">{new Date(timeline.discharge_time).toLocaleString()}</p>
                </div>
              )}
              <div>
                <span className="text-xs text-gray-500">Events</span>
                <p className="text-lg font-bold text-medical-600">{events.length}</p>
              </div>
              {groups.length > 0 && (
                <div>
                  <span className="text-xs text-gray-500">Groups</span>
                  <p className="text-lg font-bold text-source-600">{groups.length}</p>
                </div>
              )}
            </div>

            {/* Quality indicators */}
            {timeline.quality_report && (
              <div className="mt-3 flex flex-wrap gap-3 text-xs">
                <span className="px-2 py-1 bg-danger-50 text-danger-700 rounded-lg">
                  ⚠️ Abnormal: {timeline.quality_report.abnormal_events}
                </span>
                <span className="px-2 py-1 bg-warning-50 text-warning-700 rounded-lg">
                  ~ Uncertain: {timeline.quality_report.uncertain_events}
                </span>
              </div>
            )}
          </div>

          {/* Filter bar */}
          <div className="flex flex-wrap gap-2 mb-6">
            <button
              onClick={() => setFilterCat("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filterCat === "all" ? "bg-gray-800 text-white" : "bg-white text-gray-600 border border-gray-200 hover:border-gray-400"
              }`}
            >
              All ({events.length})
            </button>
            {categories.map((cat: string) => {
              const cfg = CATEGORY_CONFIG[cat] || {};
              const count = events.filter((e: any) => e.category === cat).length;
              return (
                <button
                  key={cat}
                  onClick={() => setFilterCat(cat)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    filterCat === cat ? `${cfg.bg} ${cfg.color} border border-transparent` : "bg-white text-gray-600 border border-gray-200 hover:border-gray-400"
                  }`}
                >
                  {cfg.icon} {cat.replace(/_/g, " ")} ({count})
                </button>
              );
            })}
          </div>

          {/* Timeline */}
          <div className="relative">
            <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

            {filteredEvents.map((event: any) => {
              const cfg = CATEGORY_CONFIG[event.category] || { icon: "•", color: "text-gray-600", bg: "bg-gray-100" };
              return (
                <motion.div
                  key={event.event_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="relative pl-14 pr-4 py-2 cursor-pointer hover:bg-gray-50 rounded-lg transition-colors"
                  onClick={() => setSelectedEvent(selectedEvent?.event_id === event.event_id ? null : event)}
                >
                  <div className={`absolute left-5 w-3 h-3 rounded-full border-2 border-white shadow ${cfg.bg}`} />

                  <div className="flex items-start gap-2">
                    <span className="text-sm">{cfg.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[11px] font-mono text-gray-400">
                          {new Date(event.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                        <span className="text-sm font-medium text-gray-900 truncate">{event.label}</span>
                        {event.is_abnormal && (
                          <span className="px-1.5 py-0.5 bg-danger-100 text-danger-700 rounded text-[10px] font-bold">⚠ ABNORMAL</span>
                        )}
                        {event.uncertainty && (
                          <span className="px-1.5 py-0.5 bg-warning-100 text-warning-700 rounded text-[10px] font-bold">~ {event.uncertainty}</span>
                        )}
                      </div>
                      {/* Inline value preview */}
                      {event.detail?.value != null && event.category === "lab_result" && (
                        <span className="text-xs text-gray-500 mt-0.5">
                          Value: {String(event.detail.value)} {event.detail.uom || ""}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Expanded event detail */}
                  {selectedEvent?.event_id === event.event_id && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="mt-2 ml-6 bg-gray-50 border border-gray-200 rounded-lg p-3"
                    >
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {Object.entries(event.detail || {}).map(([k, v]) => (
                          <div key={k}>
                            <span className="text-gray-400">{k}: </span>
                            <span className="text-gray-700 font-medium">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                      {/* Source trace */}
                      <div className="mt-3 flex items-center gap-2 bg-source-50 border border-source-200 rounded-lg px-3 py-2">
                        <Database className="w-3.5 h-3.5 text-source-500" />
                        <span className="text-[11px] font-mono text-source-700">
                          {event.source.collection} · row {event.source.doc_id}
                        </span>
                        <span className="text-[10px] text-source-500">· {event.source.fields}</span>
                        <span className="ml-auto text-[9px] bg-source-200 text-source-800 px-1.5 rounded font-bold">SOURCE</span>
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              );
            })}

            {/* Event Groups */}
            {groups.map((group: any) => {
              const cfg = CATEGORY_CONFIG[group.category] || { icon: "📊", color: "text-source-600", bg: "bg-source-50" };
              const isExpanded = expandedGroups.has(group.group_id);
              return (
                <div key={group.group_id} className="relative pl-14 pr-4 py-2">
                  <div className={`absolute left-5 w-3 h-3 rounded-full border-2 border-white shadow ${cfg.bg}`} />
                  <div
                    className="bg-gray-50 border border-gray-200 rounded-xl p-3 cursor-pointer hover:border-gray-300"
                    onClick={() => {
                      const next = new Set(expandedGroups);
                      isExpanded ? next.delete(group.group_id) : next.add(group.group_id);
                      setExpandedGroups(next);
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm">{cfg.icon}</span>
                        <span className="text-sm font-medium text-gray-700">
                          {group.category.replace(/_/g, " ")}
                        </span>
                        <span className="text-xs text-gray-400">({group.event_count} events)</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {group.summary_stats?.mean !== undefined && (
                          <span className="text-xs text-gray-500">
                            Mean: <strong>{group.summary_stats.mean}</strong> | Range: [{group.summary_stats.min}, {group.summary_stats.max}]
                          </span>
                        )}
                        {isExpanded ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                      </div>
                    </div>
                    <div className="mt-1 text-[11px] text-source-500 font-mono">
                      🔗 {group.member_source_traces?.length || 0} source traces preserved
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {!timeline && !loading && (
        <div className="text-center py-20">
          <Activity className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Enter a hospital admission ID to build the timeline</p>
        </div>
      )}
    </div>
  );
};

export default TimelinePage;