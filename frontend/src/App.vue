<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<template>
  <AppLayout v-if="!route.meta.hideLayout">
    <router-view />
  </AppLayout>
  <router-view v-else />
</template>
