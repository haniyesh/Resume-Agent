import { useRef, useState } from 'react'
import { extractTitles } from '../api.js'

export default function ResumeUpload({ onTitles, disabled }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  async function handleUpload() {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const data = await extractTitles(file)
      onTitles(data.titles)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card">
      <h2>3. Upload your resume</h2>
      <p className="muted">We'll extract the job titles from your PDF.</p>

      <div className="row">
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          hidden
        />
        <button
          type="button"
          className="secondary"
          onClick={() => inputRef.current?.click()}
        >
          {file ? file.name : 'Choose PDF'}
        </button>
        <button
          type="button"
          onClick={handleUpload}
          disabled={!file || loading || disabled}
        >
          {loading ? 'Extracting...' : 'Extract job titles'}
        </button>
      </div>

      {error && <p className="error">{error}</p>}
    </section>
  )
}
