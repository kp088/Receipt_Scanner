import { formatDate, formatMoney } from '../format.js'

export default function HistoryList({ receipts, selectedId, onSelect, search, onSearch }) {
  return (
    <div className="panel history">
      <div className="history-head">
        <h2>History</h2>
        <input
          type="search"
          placeholder="Search merchant"
          value={search}
          onChange={(event) => onSearch(event.target.value)}
        />
      </div>

      {receipts.length === 0 ? (
        <p className="muted">{search ? 'No receipts match your search.' : 'No receipts yet.'}</p>
      ) : (
        <ul className="history-list">
          {receipts.map((receipt) => (
            <li key={receipt.id}>
              <button
                className={`history-item ${receipt.id === selectedId ? 'history-item-active' : ''}`}
                onClick={() => onSelect(receipt.id)}
              >
                <span className="history-main">
                  <span className="history-merchant">{receipt.merchant}</span>
                  <span className="history-meta">
                    {formatDate(receipt.purchase_date)} · {receipt.category}
                  </span>
                </span>
                <span className="history-side">
                  <span className="history-total">
                    {formatMoney(receipt.total, receipt.currency)}
                  </span>
                  {receipt.is_sample && <span className="badge badge-sample">Sample</span>}
                  {receipt.warnings.length > 0 && <span className="badge">Review</span>}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
