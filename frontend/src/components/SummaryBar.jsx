import { formatMoney } from '../format.js'

export default function SummaryBar({ summary }) {
  if (!summary) return null

  const top = summary.by_category[0]

  return (
    <div className="summary">
      <div className="stat">
        <span className="stat-label">Receipts</span>
        <span className="stat-value">{summary.receipt_count}</span>
      </div>
      <div className="stat">
        <span className="stat-label">Total spent</span>
        <span className="stat-value">{formatMoney(summary.total_spent)}</span>
      </div>
      <div className="stat">
        <span className="stat-label">Top category</span>
        <span className="stat-value">{top ? top.category : 'None yet'}</span>
        {top && <span className="stat-note">{formatMoney(top.total)}</span>}
      </div>
    </div>
  )
}
