import { useCallback, useEffect, useState } from 'react'

import * as api from './api.js'
import HistoryList from './components/HistoryList.jsx'
import ReceiptEditor from './components/ReceiptEditor.jsx'
import SummaryBar from './components/SummaryBar.jsx'
import UploadZone from './components/UploadZone.jsx'

export default function App() {
  const [receipts, setReceipts] = useState([])
  const [summary, setSummary] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [search, setSearch] = useState('')
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState('')
  const [demoMode, setDemoMode] = useState(false)

  useEffect(() => {
    api
      .getHealth()
      .then((health) => setDemoMode(health.extractor === 'mock'))
      .catch(() => {})
  }, [])

  const selected = receipts.find((receipt) => receipt.id === selectedId) ?? null

  const refresh = useCallback(async () => {
    try {
      const [page, totals] = await Promise.all([api.listReceipts(search), api.getSummary()])
      setReceipts(page.items)
      setSummary(totals)
    } catch (err) {
      setError(err.message)
    }
  }, [search])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function handleScan(file) {
    setError('')
    setScanning(true)
    try {
      const receipt = await api.scanReceipt(file)
      await refresh()
      setSelectedId(receipt.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setScanning(false)
    }
  }

  async function handleSave(id, data) {
    setError('')
    try {
      await api.updateReceipt(id, data)
      await refresh()
      return true
    } catch (err) {
      setError(err.message)
      return false
    }
  }

  async function handleDelete(id) {
    setError('')
    try {
      await api.deleteReceipt(id)
      setSelectedId(null)
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRemoveSamples() {
    setError('')
    try {
      await api.deleteSamples()
      if (selected?.is_sample) setSelectedId(null)
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">RS</span>
          <div>
            <h1>Receipt Scanner</h1>
            <p>Snap a receipt. Get clean, structured data.</p>
          </div>
        </div>
        <a className="button button-light" href={api.exportUrl}>
          Export CSV
        </a>
      </header>

      <SummaryBar summary={summary} />

      {demoMode && (
        <div className="alert alert-info">
          <strong>Demo mode:</strong> uploads return sample receipts, not the image you chose. To
          read real receipts, set <code>EXTRACTOR=gemini</code> and <code>GEMINI_API_KEY</code> in
          the <code>.env</code> file, then restart the backend.
        </div>
      )}

      {summary?.sample_count > 0 && (
        <div className="alert alert-note">
          <span>
            <strong>Note:</strong> the receipts marked <span className="badge badge-sample">Sample</span>{' '}
            are just examples to show how the app works. You can edit or delete them.
          </span>
          <button className="link-button" onClick={handleRemoveSamples}>
            Remove samples
          </button>
        </div>
      )}

      {error && (
        <div className="alert alert-error" role="alert">
          <span>{error}</span>
          <button className="link-button" onClick={() => setError('')}>
            Dismiss
          </button>
        </div>
      )}

      <main className="layout">
        <aside className="sidebar">
          <UploadZone onFile={handleScan} busy={scanning} />
          <HistoryList
            receipts={receipts}
            selectedId={selectedId}
            onSelect={setSelectedId}
            search={search}
            onSearch={setSearch}
          />
        </aside>

        <section className="panel workspace">
          {selected ? (
            // The key resets the form whenever a different receipt is opened.
            <ReceiptEditor
              key={selected.id}
              receipt={selected}
              onSave={handleSave}
              onDelete={handleDelete}
            />
          ) : (
            <div className="empty">
              <h2>No receipt selected</h2>
              <p>Upload a receipt photo or pick one from your history to review it.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
