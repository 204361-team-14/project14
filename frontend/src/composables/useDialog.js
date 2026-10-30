import { reactive } from 'vue'

const defaults = {
  type: 'confirm',
  title: '',
  message: '',
  confirmText: 'ตกลง',
  cancelText: 'ยกเลิก',
  variant: 'default'
}

export const dialogState = reactive({ open: false, ...defaults })

let resolver = null

function openDialog(options) {
  // ถ้ามีกล่องค้างอยู่ ให้ปิดอันเก่าแบบ "ยกเลิก" ก่อน
  if (resolver) resolver(false)

  return new Promise((resolve) => {
    resolver = resolve
    Object.assign(dialogState, defaults, options, { open: true })
  })
}

export function resolveDialog(result) {
  dialogState.open = false
  const done = resolver
  resolver = null
  if (done) done(result)
}

export function confirmDialog(message, options = {}) {
  return openDialog({
    type: 'confirm',
    title: 'ยืนยันการดำเนินการ',
    confirmText: 'ยืนยัน',
    message,
    ...options
  })
}

export function alertDialog(message, options = {}) {
  return openDialog({
    type: 'alert',
    title: 'แจ้งเตือน',
    confirmText: 'ตกลง',
    variant: 'warning',
    message,
    ...options
  }).then(() => undefined)
}
