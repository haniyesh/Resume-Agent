import { useState } from 'react'
import ResumeUpload from './components/ResumeUpload.jsx'
import JobTitles from './components/JobTitles.jsx'
import JobResults from './components/JobResults.jsx'
import { searchJobs } from './api.js'
import './App.css'

function App() {
  const [titles, setTitles] = useState([])
  const [selected, setSelected] = useState([])
  const [location, setLocation] = useState('')
  const [jobs, setJobs] = useState([])
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function handleTitles(newTitles) {
    setTitles([...new Set(newTitles)])
    setSelected([])
    setJobs([])
    setCount(0)
  }

  function handleSearch() {
    if (!selected.length) {
      setError('Select at least one job title to search.  Select jobs at the top are in the input box.')
      return
    }
    setLoading(true)
    setError('')
    ;(async () => {
      const allJobs = []
      let total = 0
      const failed = []
      for (const title of selected) {
        try {
          const data = await searchJobs(title, location.trim())
          allJobs.push(...data.jobs)
          total += data.count ?? 0
        } catch (err) {
          failed.push(`${title}: ${err.message}`)
        }
      }
      setJobs(allJobs)
      setCount(total)
      if (failed.length) setError(failed.join('\n'))
      setLoading(false)
    })()
  }

  return (
    <div className="dashboard">
      <header>
        <h1>Resume Job Dashboard</h1>
        <p className="muted">Pick roles at the top, then search. Upload a resume to extract titles.</p>
      </header>

      <JobTitles
        titles={titles}
        setTitles={setTitles}
        selected={selected}
        setSelected={setSelected}
        location={location}
        setLocation={setLocation}
        onSearch={handleSearch}
        loading={loading}
        error={error}
      />

      <ResumeUpload onTitles={handleTitles} disabled={loading} />

      <JobResults jobs={jobs} count={count} />
    </div>
  )
}

export default App
