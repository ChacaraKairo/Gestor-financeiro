<script setup>
import { computed } from 'vue'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'
import { Pie, Bar } from 'vue-chartjs'

// Registro dos componentes do Chart.js
ChartJS.register(ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const props = defineProps({
  transacoes: Array,
  historico: Array,
  meses: Array
})

// Lógica da Pizza
const pieData = computed(() => {
  const despesas = props.transacoes.filter((t) => t.category && t.category.type === 'DESPESA')
  const agrupado = {}
  const cores = []
  despesas.forEach((t) => {
    const nome = t.category.name
    if (!agrupado[nome]) {
      agrupado[nome] = 0
      cores.push(t.category.color_hex || '#ccc')
    }
    agrupado[nome] += Number(t.amount)
  })
  return {
    labels: Object.keys(agrupado),
    datasets: [{ backgroundColor: cores, data: Object.values(agrupado) }]
  }
})

// Lógica das Barras
const barData = computed(() => {
  return {
    labels: props.meses.map((m) => m.n.substr(0, 3)),
    datasets: [
      {
        label: 'Receitas',
        backgroundColor: '#2ecc71',
        data: props.historico.map((h) => h.receita)
      },
      { label: 'Despesas', backgroundColor: '#e74c3c', data: props.historico.map((h) => h.despesa) }
    ]
  }
})

const pieOptions = { responsive: true, maintainAspectRatio: false }
const barOptions = { responsive: true, maintainAspectRatio: false }
</script>

<template>
  <div class="section-charts-col">
    <div class="chart-card">
      <h3>Despesas por Categoria</h3>
      <div class="chart-box">
        <Pie v-if="transacoes.length > 0" :data="pieData" :options="pieOptions" />
        <p v-else class="empty-msg">Sem dados para gráfico.</p>
      </div>
    </div>
    <div class="chart-card">
      <h3>Evolução Anual</h3>
      <div class="chart-box">
        <Bar :data="barData" :options="barOptions" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-charts-col {
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}
.chart-card {
  background: white;
  padding: 15px;
  border-radius: 10px;
  flex: 1;
  min-height: 250px;
  display: flex;
  flex-direction: column;
}
.chart-card h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #666;
}
.chart-box {
  flex: 1;
  position: relative;
}
.empty-msg {
  text-align: center;
  color: #999;
  font-size: 13px;
  margin-top: 10px;
}
</style>
