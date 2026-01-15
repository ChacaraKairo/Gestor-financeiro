<script setup>
defineProps({
  resumo: Object,
  money: Function
})
</script>

<template>
  <div class="kpi-container">
    <div class="card receita">
      <h3>Receitas</h3>
      <p class="valor">{{ money(resumo.receita) }}</p>
    </div>
    <div class="card despesa">
      <h3>Despesas</h3>
      <p class="valor">{{ money(resumo.despesa) }}</p>
    </div>
    <div class="card saldo" :class="{ negativo: resumo.saldo < 0 }">
      <h3>Saldo</h3>
      <p class="valor">{{ money(resumo.saldo) }}</p>
    </div>
    <div class="card pendente">
      <h3>A Pagar (Pendente)</h3>
      <p class="valor">{{ money(resumo.pendente) }}</p>
    </div>
  </div>
</template>

<style scoped>
.kpi-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 20px;
  flex-shrink: 0;
}
.card {
  background: white;
  padding: 15px;
  border-radius: 10px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
  text-align: center;
}
.card h3 {
  font-size: 11px;
  text-transform: uppercase;
  color: #888;
  margin-bottom: 5px;
}
.card .valor {
  font-size: 22px;
  font-weight: 700;
  color: #333;
}
.receita .valor {
  color: #2ecc71;
}
.despesa .valor {
  color: #e74c3c;
}
.saldo.negativo .valor {
  color: #e74c3c;
}
.pendente .valor {
  color: #f39c12;
}
</style>
