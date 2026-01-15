<script setup>
import Dashboard from './components/Dashboard.vue'
</script>

<template>
  <div class="app-container">
    <Dashboard />
  </div>
</template>

<style>
/* Reset básico para tirar margens brancas do navegador */
body {
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f4f7f6;
  color: #333;
}

.app-container {
  min-height: 100vh;
}
</style>
