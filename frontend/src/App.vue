<script setup>
import "tailwindcss";
import { ref, onMounted } from 'vue'

const message = ref('Loading...')

onMounted(async () => {
  const response = await fetch('http://localhost:5000/api/test')
  const data = await response.json()

  message.value = data.message
})
</script>

<template>
  
  <div class="min-h-screen bg-gray-100 flex items-center justify-center">
    <div class="bg-white p-8 rounded-xl shadow-lg">
      <h1 class="text-3xl font-bold text-blue-600">
        Building Service Management
      </h1>
      <div class="p-8">
        <h1 class="text-3xl font-bold">
      {{ message }}
        </h1>
      </div>
      <p class="mt-2 text-gray-600">
        Vue + Tailwind is working!
      </p>
    </div>
  </div>
</template>
