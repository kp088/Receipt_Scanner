import { useState } from 'react'

import { imageUrl } from '../api.js'
import { CATEGORIES } from '../format.js'

// Form inputs work with strings, so numbers are converted on the way in and out.
const toText = (value) => (value === null || value === undefined ? '' : String(value))
const toNumberOrNull = (text) => (text === '' ? null : Number(text))

function toDraft(receipt) {
  return {
    merchant: receipt.merchant,
    purchase_date: receipt.purchase_date ?? '',
    currency: receipt.currency,
    category: receipt.category,
    payment_method: receipt.payment_method ?? '',
    subtotal: toText(receipt.subtotal),
    tax: toText(receipt.tax),
    total: toText(receipt.total),
    items: receipt.items.map((item) => ({
      description: item.description,
      quantity: toText(item.quantity),
      amount: toText(item.amount),
    })),
  }
}

function toPayload(draft) {
  return {
    merchant: draft.merchant.trim(),
    purchase_date: draft.purchase_date || null,
    currency: draft.currency.trim(),
    category: draft.category,
    payment_method: draft.payment_method.trim() || null,
    subtotal: toNumberOrNull(draft.subtotal),
    tax: toNumberOrNull(draft.tax),
    total: Number(draft.total || 0),
    items: draft.items
      .filter((item) => item.description.trim() !== '')
      .map((item) => ({
        description: item.description.trim(),
        quantity: Number(item.quantity || 1),
        amount: Number(item.amount || 0),
      })),
  }
}

export default function ReceiptEditor({ receipt, onSave, onDelete }) {
  const [draft, setDraft] = useState(() => toDraft(receipt))
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  // Delete asks for a second click before anything is removed.
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  function setField(name, value) {
    setDraft((current) => ({ ...current, [name]: value }))
    setSaved(false)
  }

  function setItem(index, name, value) {
    setDraft((current) => ({
      ...current,
      items: current.items.map((item, i) => (i === index ? { ...item, [name]: value } : item)),
    }))
    setSaved(false)
  }

  function addItem() {
    setField('items', [...draft.items, { description: '', quantity: '1', amount: '' }])
  }

  function removeItem(index) {
    setField('items', draft.items.filter((_, i) => i !== index))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    const ok = await onSave(receipt.id, toPayload(draft))
    setSaving(false)
    setSaved(ok)
  }

  return (
    <div className="editor">
      {receipt.has_image && (
        <div className="preview">
          <img src={imageUrl(receipt.id)} alt={`Receipt from ${receipt.merchant}`} />
        </div>
      )}

      <form className="editor-form" onSubmit={handleSubmit}>
        <h2>Review and correct</h2>

        {receipt.warnings.length > 0 && (
          <div className="alert alert-warning">
            <strong>Please double-check this receipt</strong>
            <ul>
              {receipt.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="fields">
          <label className="field field-wide">
            Merchant
            <input
              required
              value={draft.merchant}
              onChange={(event) => setField('merchant', event.target.value)}
            />
          </label>
          <label className="field">
            Date
            <input
              type="date"
              value={draft.purchase_date}
              onChange={(event) => setField('purchase_date', event.target.value)}
            />
          </label>
          <label className="field">
            Category
            <select
              value={draft.category}
              onChange={(event) => setField('category', event.target.value)}
            >
              {/* Keep an unexpected category from the AI selectable instead of losing it. */}
              {!CATEGORIES.includes(draft.category) && <option>{draft.category}</option>}
              {CATEGORIES.map((category) => (
                <option key={category}>{category}</option>
              ))}
            </select>
          </label>
          <label className="field">
            Payment method
            <input
              value={draft.payment_method}
              onChange={(event) => setField('payment_method', event.target.value)}
            />
          </label>
          <label className="field">
            Currency
            <input
              required
              minLength={3}
              maxLength={3}
              value={draft.currency}
              onChange={(event) => setField('currency', event.target.value.toUpperCase())}
            />
          </label>
        </div>

        <table className="items">
          <thead>
            <tr>
              <th>Item</th>
              <th className="col-number">Qty</th>
              <th className="col-number">Amount</th>
              <th aria-label="Remove" />
            </tr>
          </thead>
          <tbody>
            {draft.items.map((item, index) => (
              <tr key={index}>
                <td>
                  <input
                    aria-label="Item description"
                    value={item.description}
                    onChange={(event) => setItem(index, 'description', event.target.value)}
                  />
                </td>
                <td className="col-number">
                  <input
                    aria-label="Quantity"
                    type="number"
                    min="0.01"
                    step="any"
                    value={item.quantity}
                    onChange={(event) => setItem(index, 'quantity', event.target.value)}
                  />
                </td>
                <td className="col-number">
                  <input
                    aria-label="Amount"
                    type="number"
                    step="0.01"
                    value={item.amount}
                    onChange={(event) => setItem(index, 'amount', event.target.value)}
                  />
                </td>
                <td>
                  <button
                    type="button"
                    className="icon-button"
                    aria-label="Remove item"
                    onClick={() => removeItem(index)}
                  >
                    ×
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button type="button" className="link-button" onClick={addItem}>
          + Add item
        </button>

        <div className="totals">
          <label className="field">
            Subtotal
            <input
              type="number"
              step="0.01"
              value={draft.subtotal}
              onChange={(event) => setField('subtotal', event.target.value)}
            />
          </label>
          <label className="field">
            Tax
            <input
              type="number"
              step="0.01"
              value={draft.tax}
              onChange={(event) => setField('tax', event.target.value)}
            />
          </label>
          <label className="field field-total">
            Total
            <input
              required
              type="number"
              min="0"
              step="0.01"
              value={draft.total}
              onChange={(event) => setField('total', event.target.value)}
            />
          </label>
        </div>

        <div className="actions">
          <button type="submit" className="button button-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save changes'}
          </button>
          {saved && <span className="saved">Saved</span>}
          {confirmingDelete ? (
            <span className="confirm-delete">
              Delete this receipt?
              <button
                type="button"
                className="button button-danger-solid"
                onClick={() => onDelete(receipt.id)}
              >
                Yes, delete
              </button>
              <button
                type="button"
                className="button button-outline"
                onClick={() => setConfirmingDelete(false)}
              >
                Cancel
              </button>
            </span>
          ) : (
            <button
              type="button"
              className="button button-danger"
              onClick={() => setConfirmingDelete(true)}
            >
              Delete
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
