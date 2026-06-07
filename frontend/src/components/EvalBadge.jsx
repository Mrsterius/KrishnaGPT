/**
 * Circular SVG progress indicator showing a RAG evaluation score.
 * score: 0.0 – 1.0
 */
export default function EvalBadge({ label, score, color }) {
  const size = 48
  const strokeWidth = 4
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - score * circumference

  return (
    <div className="eval-badge">
      <svg
        width={size}
        height={size}
        style={{ transform: 'rotate(-90deg)', display: 'block' }}
        aria-label={`${label}: ${Math.round(score * 100)}%`}
      >
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.07)"
          strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.9s ease' }}
        />
      </svg>
      {/* Centred score text */}
      <div className="eval-badge-center">
        <span className="eval-score">{Math.round(score * 100)}%</span>
      </div>
      <span className="eval-label">{label}</span>
    </div>
  )
}
