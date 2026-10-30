function pad(value) {
  return String(value).padStart(2, '0')
}

export function todayString(date = new Date()) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function timeString(date = new Date()) {
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function formatId(prefix, id) {
  return `${prefix}-${String(id).padStart(6, '0')}`
}

export function sameId(a, b) {
  if (a === null || a === undefined || b === null || b === undefined) return false
  return Number(a) === Number(b)
}
