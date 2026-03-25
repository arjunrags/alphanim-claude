import { useState } from "react"
import SearchBar from "./components/SearchBar"
import PaperCard from "./components/PaperCard"
import GraphCanvas from "./components/GraphCanvas"
import InsightPanel from "./components/InsightPanel"

export default function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeView, setActiveView] = useState("papers") // "papers" | "graph"
  const [selectedPaper, setSelectedPaper] = useState(null)

  async function handleSearch(query) {
    setLoading(true)
    setSelectedPaper(null)
    try {
      const res = await fetch("http://localhost:8000/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, k: 8 }),
      })
      const data = await res.json()
      setResults(data)
    } catch (e) {
      console.error("Search failed:", e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0d0f14] text-[#e8e6df] font-['Instrument_Serif',serif]">
      {/* Header */}
      <header className="border-b border-white/10 px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-full bg-[#c8a96e] opacity-90" />
          <span className="text-xl tracking-wide text-[#c8a96e]">Membrain Explorer</span>
        </div>
        {results && (
          <div className="flex gap-1 bg-white/5 rounded-lg p-1">
            {["papers", "graph"].map((v) => (
              <button
                key={v}
                onClick={() => setActiveView(v)}
                className={`px-4 py-1.5 rounded-md text-sm capitalize transition-all duration-200 ${
                  activeView === v
                    ? "bg-[#c8a96e] text-[#0d0f14] font-medium"
                    : "text-[#a09880] hover:text-[#e8e6df]"
                }`}
              >
                {v}
              </button>
            ))}
          </div>
        )}
      </header>

      {/* Search */}
      <div className={`transition-all duration-500 ${results ? "py-6 px-8" : "py-24 px-8"}`}>
        <SearchBar onSearch={handleSearch} loading={loading} hasResults={!!results} />
        {results && !loading && (
          <p className="mt-2 text-xs text-[#6b6858]">
            Expanded query:{" "}
            <span className="text-[#a09880] italic">"{results.expanded_query}"</span>
          </p>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="flex gap-2">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full bg-[#c8a96e] animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
          <p className="text-sm text-[#6b6858]">Searching ArXiv · Building graph · Linking papers…</p>
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <main className="px-8 pb-16">
          {activeView === "papers" && (
            <div className="flex gap-6">
              <div className="flex-1 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {results.papers.map((paper) => (
                  <PaperCard
                    key={paper.id}
                    paper={paper}
                    selected={selectedPaper?.id === paper.id}
                    onClick={() => setSelectedPaper(selectedPaper?.id === paper.id ? null : paper)}
                  />
                ))}
              </div>
              {selectedPaper && (
                <InsightPanel paper={selectedPaper} onClose={() => setSelectedPaper(null)} />
              )}
            </div>
          )}
          {activeView === "graph" && (
            <GraphCanvas query={results.query} />
          )}
        </main>
      )}

      {/* Empty state */}
      {!results && !loading && (
        <div className="flex flex-col items-center justify-center py-12 gap-3 text-center px-8">
          <p className="text-4xl opacity-20">◎</p>
          <p className="text-[#6b6858] text-sm max-w-md">
            Search any research topic. Papers are fetched from ArXiv, ranked semantically,
            and linked together in a knowledge graph via Membrain.
          </p>
        </div>
      )}
    </div>
  )
}
