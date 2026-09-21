function salaryLabel(job) {
  if (job.salary_text) return job.salary_text
  if (job.salary_min || job.salary_max) {
    return `${job.currency ?? ''} ${job.salary_min ?? ''}-${job.salary_max ?? ''}${
      job.salary_is_estimated ? ' (est.)' : ''
    }`.trim()
  }
  return ''
}

function jobUrl(job) {
  return job.url ?? job.redirect_url ?? job.apply_url ?? null
}

export default function JobResults({ jobs, count }) {
  if (!jobs.length) return null

  const remoteCount = jobs.filter((job) => job.remote).length

  return (
    <section className="card">
      <h2>4. Job results</h2>
      <p className="muted">
        Found {count ?? jobs.length} jobs — showing {jobs.length}
        {remoteCount > 0 ? ` (${remoteCount} remote)` : ''}
      </p>

      <ul className="jobs">
        {jobs.map((job) => {
          const salary = salaryLabel(job)
          const meta = [
            job.remote ? 'Remote' : '',
            job.location ? String(job.location) : '',
            salary,
          ]
            .filter(Boolean)
            .join(' · ')
          const url = jobUrl(job)
          return (
            <li key={job.id} className="job">
              <div className="job-head">
                <strong>{job.title}</strong>
                <span className="company">{job.company}</span>
              </div>
              <div className="job-meta">{meta}</div>
              {url && (
                <a href={url} target="_blank" rel="noreferrer">
                  View listing
                </a>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
