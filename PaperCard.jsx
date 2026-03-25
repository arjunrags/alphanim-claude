export default function PaperCard({ paper, selected, onClick }) {
  const topicTags = paper.tags
    .filter((t) => t.startsWith("topic."))
    .slice(0, 3)
    .map((t) => t.replace("topic.", ""))

  return (
    <div
      onClick={onClick}
      className={`group cursor-pointer rounded-xl border p-5 transition-all duration-200
        ${selected
          ? "border-[#c8a96e]/60 bg-[#c8a96e]/8"
          : "border-white/8 bg-white/3 hover:border-white/20 hover:bg-white/5"
        }`}
    >
      {/* Year + linked badge */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-[#6b6858]">{paper.year || "—"}</span>
        {paper.memory_id && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#c8a96e]/15 text-[#c8a96e] border border-[#c8a96e]/20">
            ◈ linked
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="text-sm font-medium text-[#e8e6df] leading-snug mb-2 line-clamp-3">
        {paper.title}
      </h3>

      {/* Authors */}
      <p className="text-xs text-[#6b6858] mb-3 truncate">
        {paper.authors?.slice(0, 3).join(", ")}
        {paper.authors?.length > 3 ? " et al." : ""}
      </p>

      {/* Abstract preview */}
      <p className="text-xs text-[#7a7868] line-clamp-3 leading-relaxed mb-4">
        {paper.abstract}
      </p>

      {/* Tags */}
      <div className="flex flex-wrap gap-1.5">
        {topicTags.map((tag) => (
          <span
            key={tag}
            className="text-[10px] px-2 py-0.5 rounded bg-white/5 text-[#7a7868] border border-white/8"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* ArXiv link */}
      {paper.arxiv_url && (
        <a
          href={paper.arxiv_url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="mt-3 inline-block text-[10px] text-[#c8a96e]/70 hover:text-[#c8a96e] transition-colors"
        >
          View on ArXiv →
        </a>
      )}
    </div>
  )
}
