import { useRef, useState } from 'react'

export default function UploadZone({ onFile, busy }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  function handleDrop(event) {
    event.preventDefault()
    setDragging(false)
    const file = event.dataTransfer.files[0]
    if (file && !busy) onFile(file)
  }

  function handleChange(event) {
    const file = event.target.files[0]
    if (file) onFile(file)
    // Clear the input so the same file can be chosen twice in a row.
    event.target.value = ''
  }

  return (
    <div
      className={`dropzone ${dragging ? 'dropzone-active' : ''}`}
      onDragOver={(event) => {
        event.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        hidden
        onChange={handleChange}
      />

      {busy ? (
        <>
          <div className="spinner" />
          <p className="dropzone-title">Reading your receipt…</p>
        </>
      ) : (
        <>
          <p className="dropzone-title">Drop a receipt photo here</p>
          <p className="dropzone-hint">JPG, PNG or WEBP, up to 8 MB</p>
          <button className="button button-primary" onClick={() => inputRef.current.click()}>
            Choose file
          </button>
        </>
      )}
    </div>
  )
}
