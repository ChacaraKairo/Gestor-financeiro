<script setup>
defineProps({
  transacoes: Array,
  money: Function,
  formatDate: Function
})

const emit = defineEmits(['editar', 'excluir', 'novo'])
</script>

<template>
  <div class="section-table">
    <div class="section-header">
      <h2>Lançamentos</h2>
      <button class="btn-add" @click="emit('novo')">+ Novo</button>
    </div>
    <div class="table-container">
      <table v-if="transacoes.length > 0">
        <thead>
          <tr>
            <th>Data</th>
            <th>Descrição</th>
            <th>Categoria</th>
            <th>Status</th>
            <th>Valor</th>
            <th style="text-align: right">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in transacoes" :key="t.id">
            <td>{{ formatDate(t.transaction_date) }}</td>
            <td>
              {{ t.description }}<br />
              <small v-if="!t.is_paid" class="status-pending">Pendente</small>
            </td>
            <td>
              <span class="badge" :style="{ backgroundColor: t.category?.color_hex }">
                {{ t.category?.name }}
              </span>
            </td>
            <td>
              <span v-if="t.is_paid" class="status-ok">Pago</span>
              <span v-else class="status-pending">Pendente</span>
            </td>
            <td :class="t.category?.type === 'DESPESA' ? 'text-red' : 'text-green'">
              {{ t.category?.type === 'DESPESA' ? '- ' : '+ ' }}
              {{ money(t.amount) }}
            </td>
            <td style="text-align: right">
              <button class="btn-icon edit" @click="emit('editar', t)">✏️</button>
              <button class="btn-icon trash" @click="emit('excluir', t.id)">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty-msg">Nenhum lançamento neste mês.</p>
    </div>
  </div>
</template>

<style scoped>
.section-table {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.table-container {
  overflow-y: auto;
  flex: 1;
  -webkit-app-region: no-drag !important;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th {
  text-align: left;
  color: #888;
  font-size: 12px;
  padding: 8px;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  background: white;
}
td {
  padding: 10px 8px;
  border-bottom: 1px solid #f9f9f9;
  font-size: 13px;
}
.status-ok {
  color: #2ecc71;
  font-weight: bold;
  font-size: 11px;
  background: #eafaf1;
  padding: 2px 6px;
  border-radius: 4px;
}
.status-pending {
  color: #e67e22;
  font-weight: bold;
  font-size: 11px;
  background: #fef5e7;
  padding: 2px 6px;
  border-radius: 4px;
  display: block;
}
.badge {
  color: white;
  padding: 3px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: bold;
}
.text-red {
  color: #e74c3c;
  font-weight: 500;
}
.text-green {
  color: #2ecc71;
  font-weight: 500;
}
.btn-add {
  background: #333;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 5px;
  cursor: pointer;
  -webkit-app-region: no-drag;
}
.btn-icon {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  margin-left: 5px;
  opacity: 0.6;
  -webkit-app-region: no-drag;
}
.empty-msg {
  text-align: center;
  color: #999;
  font-size: 13px;
  margin-top: 10px;
}
</style>
