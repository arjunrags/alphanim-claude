import { useEffect, useState } from "react"

export default function InsightPanel({ paper, onClose }) {
  const [insight, setInsight] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!paper) return
    fetchInsight()
  }, [paper.id])

  async function fetchInsight() {
    setLoading(true)
    setInsight(null)
    try {
      const res = await fetch("http://localhost:8000/api/memories/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: paper.title, k: 5 }),
      })
      const data = await res.json()
      setInsight(data)
    } catch (e) {
      console.error("Insight fetch failed:", e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-80 shrink-0 rounded-xl border border-white/8 bg-white/3 p-5 h-fit sticky top-4">
      <div className="flex items-start justify-between mb-4">
        <span className="text-xs text-[#c8a96e]">◈ Membrain Insights</span>
        <button
          onClick={onClose}
          className="text-[#4a4840] hover:text-[#e8e6df] text-xs transition-colors"
        >
          ✕
        </button>
      </div>

      <h3 className="text-sm text-[#e8e6df] font-medium leading-snug mb-4 line-clamp-3">
        {paper.title}
      </h3>

      {loading && (
        <div className="text-xs text-[#4a4840] animate-pulse">Querying memory graph…</div>
      )}

      {insight && !loading && (
        <div className="space-y-3">
          {insight.answer_summary && (
            <div>
              <p className="text-[10px] uppercase tracking-widest text-[#4a4840] mb-1">Summary</p>
              <p className="text-xs text-[#a09880] leading-relaxed">{insight.answer_summary}</p>
            </div>
          )}

          {insight.key_facts?.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-widest text-[#4a4840] mb-1">Key facts</p>
              <ul className="space-y-1">
                {insight.key_facts.slice(0, 4).map((fact, i) => (
                  <li key={i} className="text-xs text-[#7a7868] leading-relaxed flex gap-2">
                    <span className="text-[#c8a96e] shrink-0">·</span>
                    {fact}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {insight.important_relationships?.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-widest text-[#4a4840] mb-1">Related concepts</p>
              <ul className="space-y-1">
                {insight.important_relationships.slice(0, 3).map((rel, i) => (
                  <li key={i} className="text-xs text-[#7a7868] leading-relaxed flex gap-2">
                    <span className="text-[#c8a96e] shrink-0">↔</span>
                    {rel}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {insight.confidence && (
            <div className="pt-2 border-t border-white/5">
              <p className="text-[10px] text-[#3a3830]">
                confidence: {Math.round(insight.confidence * 100)}%
              </p>
            </div>
          )}
        </div>
      )}

      {insight && !loading && !insight.answer_summary && (
        <p className="text-xs text-[#4a4840]">No insights yet — search more related papers to build the graph.</p>
      )}
    </div>
  )
}
