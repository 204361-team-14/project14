import { onBeforeUnmount, ref } from 'vue'

export function useImageUploader(max = 6) {
  const files = ref([])
  const previews = ref([])
  const notice = ref('')

  function revokeAll() {
    previews.value.forEach((preview) => URL.revokeObjectURL(preview.url))
  }

  function rebuild() {
    revokeAll()
    previews.value = files.value.map((file) => ({
      name: file.name,
      url: URL.createObjectURL(file)
    }))
  }

  function onChange(event) {
    const selected = Array.from(event.target.files || [])
    notice.value = ''

    const keyOf = (file) => `${file.name}-${file.size}-${file.lastModified}`
    const existing = new Set(files.value.map(keyOf))
    let skipped = 0

    for (const file of selected) {
      const key = keyOf(file)
      if (existing.has(key)) continue

      if (files.value.length >= max) {
        skipped++
        continue
      }

      files.value.push(file)
      existing.add(key)
    }

    if (skipped > 0) {
      notice.value = `เลือกรูปได้สูงสุด ${max} รูป ระบบไม่ได้เพิ่มอีก ${skipped} รูป`
    }

    rebuild()
    event.target.value = ''
  }

  function remove(index) {
    files.value.splice(index, 1)
    notice.value = ''
    rebuild()
  }

  function clear() {
    revokeAll()
    files.value = []
    previews.value = []
    notice.value = ''
  }

  onBeforeUnmount(revokeAll)

  return { files, previews, notice, max, onChange, remove, clear }
}
