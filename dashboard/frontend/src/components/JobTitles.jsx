import { useState } from 'react'

export default function JobTitles({
  titles,
  setTitles,
  selected,
  setSelected,
  location,
  setLocation,
  onSearch,
  loading,
  error,
}) {
  const [draft, setDraft] = useState('')

  function toggle(title) {
    setSelected(
      selected.includes(title)
        ? selected.filter((t) => t !== title)
        : [...selected, title],
    )
  }

  function addTitle() {
    const title = draft.trim()
    if (!title || titles.includes(title)) return
    setTitles([...titles, title])
    setDraft('')
  }

  function removeTitle(title) {
    setTitles(titles.filter((t) => t !== title))
    setSelected(selected.filter((t) => t !== title))
  }

  return (
    <section className="card">
      <h2>1. Choose job titles</h2>
      <p className="muted">Click a job title to select it. Select as many as you like.</p>

      <ul className="chips">
        {titles.map((title) => {
          const active = selected.includes(title)
          return (
            <li key={title} className={active ? 'chip active' : 'chip'}>
              <button type="button" onClick={() => toggle(title)}>
                {active ? '✓ ' : ''}
                {title}
              </button>
              <button
                type="button"
                className="remove"
                aria-label={`Remove ${title}`}
                onClick={() => removeTitle(title)}
              >
                ×
              </button>
            </li>
          )
        })}
        {titles.length === 0 && <li className="muted">No titles yet.</li>}
      </ul>

      <div className="row">
        <input
          type="text"
          value={draft}
          placeholder="Add a job title"
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addTitle()}
        />
        <button type="button" className="secondary" onClick={addTitle}>
          Add
        </button>
      </div>

      <div className="row">
        <input
          type="text"
          placeholder="Location (optional)"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <button type="button" onClick={onSearch} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
    </section>
  )
}
