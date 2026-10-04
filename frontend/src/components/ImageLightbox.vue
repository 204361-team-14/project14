<script setup>
import { computed, onBeforeUnmount, onMounted } from 'vue'

const props = defineProps({
  images: {
    type: Array,
    default: () => []
  },
  index: {
    type: Number,
    default: -1
  }
})

const emit = defineEmits(['close', 'update:index'])

const currentImage = computed(() => {
  if (props.index < 0 || props.index >= props.images.length) {
    return ''
  }

  return props.images[props.index]
})

function close() {
  emit('close')
}

function previous() {
  if (!props.images.length) return

  const nextIndex = (
    props.index - 1 + props.images.length
  ) % props.images.length

  emit('update:index', nextIndex)
}

function next() {
  if (!props.images.length) return

  const nextIndex = (
    props.index + 1
  ) % props.images.length

  emit('update:index', nextIndex)
}

function onKeydown(event) {
  if (props.index < 0) return

  if (event.key === 'Escape') {
    close()
  } else if (event.key === 'ArrowLeft') {
    previous()
  } else if (event.key === 'ArrowRight') {
    next()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="index >= 0 && currentImage"
      class="image-lightbox"
      role="dialog"
      aria-modal="true"
      @click.self="close"
    >
      <button
        class="image-lightbox-close"
        type="button"
        aria-label="ปิดรูป"
        @click="close"
      >
        <i class="fa-solid fa-xmark"></i>
      </button>

      <button
        v-if="images.length > 1"
        class="image-lightbox-nav previous"
        type="button"
        aria-label="รูปก่อนหน้า"
        @click.stop="previous"
      >
        <i class="fa-solid fa-chevron-left"></i>
      </button>

      <figure class="image-lightbox-content">
        <img
          :src="`/uploads/${currentImage}`"
          alt="รูปภาพประกอบ"
        >

        <figcaption v-if="images.length > 1">
          {{ index + 1 }} / {{ images.length }}
        </figcaption>
      </figure>

      <button
        v-if="images.length > 1"
        class="image-lightbox-nav next"
        type="button"
        aria-label="รูปถัดไป"
        @click.stop="next"
      >
        <i class="fa-solid fa-chevron-right"></i>
      </button>
    </div>
  </Teleport>
</template>
