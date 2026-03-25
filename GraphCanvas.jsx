import { useEffect, useRef, useState } from "react"
import * as d3 from "d3"

export default function GraphCanvas({ query }) {
  const svgRef = useRef(null)
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tooltip, setTooltip] = useState(null)

  useEffect(() => {
    fetchGraph()
  }, [query])

  async function fetchGraph() {
    setLoading(true)
    try {
      const res = await fetch("http://localhost:8000/api/graph")
      const data = await res.json()
      setGraphData(data)
    } catch (e) {
      console.error("Graph fetch failed:", e)
      setGraphData({ nodes: [], edges: [] })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!graphData || !svgRef.current) return
    renderGraph(graphData)
  }, [graphData])

  function renderGraph(data) {
    const el = svgRef.current
    const width = el.clientWidth
    const height = el.clientHeight

    d3.select(el).selectAll("*").remove()

    const svg = d3.select(el)
      .attr("viewBox", `0 0 ${width} ${height}`)

    // Zoom
    const g = svg.append("g")
    svg.call(
      d3.zoom()
        .scaleExtent([0.2, 4])
        .on("zoom", (event) => g.attr("transform", event.transform))
    )

    if (!data.nodes.length) {
      svg.append("text")
        .attr("x", width / 2).attr("y", height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#4a4840")
        .attr("font-size", 14)
        .text("No graph data yet — run a search first")
      return
    }

    const nodes = data.nodes.map((n) => ({ ...n }))
    const links = data.edges.map((e) => ({ ...e }))

    // Force simulation
    const sim = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance(120).strength(0.5))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(40))

    // Edges
    const link = g.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#c8a96e")
      .attr("stroke-opacity", 0.25)
      .attr("stroke-width", 1)

    // Nodes
    const node = g.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .attr("cursor", "pointer")
      .call(
        d3.drag()
          .on("start", (event, d) => {
            if (!event.active) sim.alphaTarget(0.3).restart()
            d.fx = d.x; d.fy = d.y
          })
          .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y })
          .on("end", (event, d) => {
            if (!event.active) sim.alphaTarget(0)
            d.fx = null; d.fy = null
          })
      )

    // Node circle
    node.append("circle")
      .attr("r", 20)
      .attr("fill", "#1e2028")
      .attr("stroke", "#c8a96e")
      .attr("stroke-opacity", 0.5)
      .attr("stroke-width", 1)

    // Node label (truncated)
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", 34)
      .attr("fill", "#7a7868")
      .attr("font-size", 9)
      .text((d) => d.title.slice(0, 28) + (d.title.length > 28 ? "…" : ""))

    // Year badge
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("fill", "#c8a96e")
      .attr("font-size", 9)
      .text((d) => d.year || "")

    // Hover tooltip
    node
      .on("mouseenter", (event, d) => {
        d3.select(event.currentTarget).select("circle")
          .attr("stroke-opacity", 1)
          .attr("r", 24)
        setTooltip({ title: d.title, x: event.clientX, y: event.clientY })
      })
      .on("mouseleave", (event) => {
        d3.select(event.currentTarget).select("circle")
          .attr("stroke-opacity", 0.5)
          .attr("r", 20)
        setTooltip(null)
      })

    sim.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y)
      node.attr("transform", (d) => `translate(${d.x},${d.y})`)
    })
  }

  return (
    <div className="relative w-full h-[600px] rounded-xl border border-white/8 bg-white/2 overflow-hidden">
      {loading ? (
        <div className="flex items-center justify-center h-full text-[#6b6858] text-sm">
          Loading graph…
        </div>
      ) : (
        <svg ref={svgRef} className="w-full h-full" />
      )}

      {/* Stats overlay */}
      {graphData && !loading && (
        <div className="absolute top-4 left-4 text-xs text-[#4a4840] space-y-0.5">
          <p>{graphData.nodes.length} papers</p>
          <p>{graphData.edges.length} links</p>
        </div>
      )}

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 max-w-xs bg-[#1a1c22] border border-white/10 rounded-lg px-3 py-2 text-xs text-[#e8e6df] pointer-events-none"
          style={{ left: tooltip.x + 12, top: tooltip.y - 8 }}
        >
          {tooltip.title}
        </div>
      )}

      {/* Controls hint */}
      <div className="absolute bottom-4 right-4 text-[10px] text-[#3a3830]">
        scroll to zoom · drag to pan · drag nodes
      </div>
    </div>
  )
}
