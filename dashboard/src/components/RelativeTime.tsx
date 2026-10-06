export function RelativeTime({ value }: { value?: string | null }) {
  if (!value) {
    return <span>—</span>
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return <span>—</span>
  }

  const diff = Date.now() - date.getTime()
  const seconds = Math.max(0, Math.floor(diff / 1000))

  if (seconds < 60) {
    return <span>{seconds}s ago</span>
  }

  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) {
    return <span>{minutes} minute{minutes === 1 ? '' : 's'} ago</span>
  }

  const hours = Math.floor(minutes / 60)
  if (hours < 24) {
    return <span>{hours} hour{hours === 1 ? '' : 's'} ago</span>
  }

  const days = Math.floor(hours / 24)
  return <span>{days} day{days === 1 ? '' : 's'} ago</span>
}
