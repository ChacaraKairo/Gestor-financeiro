<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import api from '../services/api'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Pie } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip, Legend)

// --- ESTADOS ---
const resumo = ref({ receita: 0, despesa: 0, saldo: 0 })
const transacoes = ref([])
const categorias = ref([])
const carregando = ref(false)

// Modais
const showModalTransacao = ref(false)
const showModalCategorias = ref(false) // Novo Modal

// Filtros
const dataAtual = new Date()
const filtros = ref({
  mes: dataAtual.getMonth() + 1,
  ano: dataAtual.getFullYear()
})

// Formulário de Transação
const form = ref({
  description: '',
  amount: '',
  date: new Date().toISOString().substr(0, 10),
  category_id: '',
  is_fixed: false,
  is_paid: true,
  payment_method: 'Pix'
})

// Formulário de Nova Categoria
const novaCategoria = ref({
  name: '',
  color_hex: '#333333',
  type: 'DESPESA'
})

const meses = [
  { v: 1, n: 'Janeiro' },
  { v: 2, n: 'Fevereiro' },
  { v: 3, n: 'Março' },
  { v: 4, n: 'Abril' },
  { v: 5, n: 'Maio' },
  { v: 6, n: 'Junho' },
  { v: 7, n: 'Julho' },
  { v: 8, n: 'Agosto' },
  { v: 9, n: 'Setembro' },
  { v: 10, n: 'Outubro' },
  { v: 11, n: 'Novembro' },
  { v: 12, n: 'Dezembro' }
]

// --- GRÁFICO ---
const chartData = computed(() => {
  const despesas = transacoes.value.filter((t) => t.category && t.category.type === 'DESPESA')
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

const chartOptions = { responsive: true, maintainAspectRatio: false }

// --- FUNÇÕES ---
async function buscarDados() {
  carregando.value = true
  try {
    const params = { month: filtros.value.mes, year: filtros.value.ano }
    const [resResumo, resTrans, resCats] = await Promise.all([
      api.get('/dashboard/summary', { params }),
      api.get('/transactions/', { params }),
      api.get('/categories/')
    ])

    resumo.value = resResumo.data
    transacoes.value = resTrans.data
    categorias.value = resCats.data
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
  } finally {
    carregando.value = false
  }
}

// Salvar Transação
async function salvarTransacao() {
  if (!form.value.description || !form.value.amount || !form.value.category_id) {
    alert('Preencha os campos obrigatórios!')
    return
  }
  try {
    const payload = { ...form.value, amount: parseFloat(form.value.amount) }
    await api.post('/transactions/', payload)
    showModalTransacao.value = false
    buscarDados()
    form.value.description = ''
    form.value.amount = '' // Limpar
  } catch (error) {
    alert('Erro ao salvar transação.')
  }
}

// --- FUNÇÕES DE CATEGORIA (NOVO) ---
async function criarCategoria() {
  if (!novaCategoria.value.name) return alert('Digite um nome!')
  try {
    await api.post('/categories/', novaCategoria.value)
    // Recarrega categorias
    const res = await api.get('/categories/')
    categorias.value = res.data
    // Limpa form
    novaCategoria.value.name = ''
    novaCategoria.value.color_hex = '#333333'
  } catch (error) {
    alert('Erro ao criar categoria')
  }
}

async function excluirCategoria(id) {
  if (!confirm('Tem certeza? Transações desta categoria ficarão sem categoria.')) return
  try {
    await api.delete(`/categories/${id}`)
    const res = await api.get('/categories/')
    categorias.value = res.data
  } catch (error) {
    alert('Erro ao excluir.')
  }
}

// Formatadores
const money = (val) => Number(val).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const formatDate = (dateString) => new Date(dateString).toLocaleDateString('pt-BR')

onMounted(() => buscarDados())
watch(filtros, () => buscarDados(), { deep: true })
</script>

<template>
  <div class="dashboard">
    <header class="top-bar">
      <div>
        <h1>Gestão Mensal</h1>
        <p class="subtitle">Controle financeiro inteligente</p>
      </div>
      <div class="filtros">
        <button class="btn-config" @click="showModalCategorias = true" title="Gerenciar Categorias">
          ⚙️ Categorias
        </button>

        <select v-model="filtros.mes">
          <option v-for="m in meses" :key="m.v" :value="m.v">{{ m.n }}</option>
        </select>
        <input type="number" v-model="filtros.ano" class="ano-input" />
        <button class="btn-refresh" @click="buscarDados">🔄</button>
      </div>
    </header>

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
    </div>

    <div class="main-content">
      <div class="section-table">
        <div class="section-header">
          <h2>Lançamentos</h2>
          <button class="btn-add" @click="showModalTransacao = true">+ Novo Lançamento</button>
        </div>

        <div class="table-container">
          <table v-if="transacoes.length > 0">
            <thead>
              <tr>
                <th>Data</th>
                <th>Descrição</th>
                <th>Categoria</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in transacoes" :key="t.id">
                <td>{{ formatDate(t.transaction_date) }}</td>
                <td>{{ t.description }}</td>
                <td>
                  <span class="badge" :style="{ backgroundColor: t.category?.color_hex }">
                    {{ t.category?.name }}
                  </span>
                </td>
                <td :class="t.category?.type === 'DESPESA' ? 'text-red' : 'text-green'">
                  {{ t.category?.type === 'DESPESA' ? '- ' : '+ ' }}
                  {{ money(t.amount) }}
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else class="empty-msg">Nenhum lançamento neste mês.</p>
        </div>
      </div>

      <div class="section-charts">
        <h2>Despesas por Categoria</h2>
        <div class="chart-box">
          <Pie v-if="transacoes.length > 0" :data="chartData" :options="chartOptions" />
          <p v-else class="empty-msg">Sem dados para gráfico.</p>
        </div>
      </div>
    </div>

    <div v-if="showModalTransacao" class="modal-overlay">
      <div class="modal-content">
        <h3>Nova Transação</h3>
        <div class="form-group">
          <label>Descrição</label>
          <input v-model="form.description" type="text" placeholder="Ex: Mercado..." />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Valor (R$)</label>
            <input v-model="form.amount" type="number" step="0.01" />
          </div>
          <div class="form-group">
            <label>Data</label>
            <input v-model="form.date" type="date" />
          </div>
        </div>
        <div class="form-group">
          <label>Categoria</label>
          <select v-model="form.category_id">
            <option value="" disabled>Selecione...</option>
            <option v-for="cat in categorias" :key="cat.id" :value="cat.id">
              {{ cat.name }} ({{ cat.type }})
            </option>
          </select>
        </div>
        <div class="form-row checkbox-row">
          <label class="checkbox-label"
            ><input type="checkbox" v-model="form.is_paid" /> Pago?</label
          >
          <label class="checkbox-label"
            ><input type="checkbox" v-model="form.is_fixed" /> Fixo?</label
          >
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showModalTransacao = false">Cancelar</button>
          <button class="btn-save" @click="salvarTransacao">Salvar</button>
        </div>
      </div>
    </div>

    <div v-if="showModalCategorias" class="modal-overlay">
      <div class="modal-content large-modal">
        <h3>Gerenciar Categorias</h3>

        <div class="add-cat-box">
          <input v-model="novaCategoria.name" type="text" placeholder="Nome da Categoria" />
          <select v-model="novaCategoria.type">
            <option value="DESPESA">Despesa</option>
            <option value="RECEITA">Receita</option>
          </select>
          <input type="color" v-model="novaCategoria.color_hex" title="Escolha a cor" />
          <button @click="criarCategoria" class="btn-mini-add">+</button>
        </div>

        <div class="cat-list">
          <div v-for="cat in categorias" :key="cat.id" class="cat-item">
            <div class="cat-info">
              <span class="color-dot" :style="{ background: cat.color_hex }"></span>
              <strong>{{ cat.name }}</strong>
              <small>({{ cat.type }})</small>
            </div>
            <button class="btn-trash" @click="excluirCategoria(cat.id)">🗑️</button>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn-cancel" @click="showModalCategorias = false">Fechar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Mantendo estilos anteriores e adicionando novos */
.dashboard {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}
.subtitle {
  color: #666;
  margin: 0;
  font-size: 14px;
}
.filtros select,
.filtros input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  margin-left: 10px;
}
.btn-refresh {
  padding: 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 1.2rem;
}
.btn-config {
  padding: 8px 15px;
  background: #eee;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  margin-right: 10px;
  font-size: 14px;
}
.btn-config:hover {
  background: #e0e0e0;
}

.kpi-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}
.card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  text-align: center;
}
.card .valor {
  font-size: 28px;
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

.main-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}
.section-table,
.section-charts {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.chart-box {
  height: 250px;
  position: relative;
}
.empty-msg {
  color: #999;
  text-align: center;
  padding: 20px;
  font-style: italic;
}

.table-container {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th {
  text-align: left;
  color: #888;
  font-size: 12px;
  padding: 10px;
  border-bottom: 1px solid #eee;
}
td {
  padding: 12px 10px;
  border-bottom: 1px solid #f9f9f9;
  font-size: 14px;
}
.text-red {
  color: #e74c3c;
  font-weight: 500;
}
.text-green {
  color: #2ecc71;
  font-weight: 500;
}
.badge {
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
}

.btn-add {
  background: #333;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.2s;
}
.btn-add:hover {
  background: #000;
  transform: translateY(-1px);
}

/* MODAL & FORMS */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 25px;
  border-radius: 12px;
  width: 400px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}
.modal-content.large-modal {
  width: 500px;
} /* Modal maior para categorias */

.form-group {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
}
.form-group label {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
  font-weight: 600;
}
.form-group input,
.form-group select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}
.form-row {
  display: flex;
  gap: 10px;
}
.form-row .form-group {
  flex: 1;
}
.checkbox-row {
  margin-bottom: 20px;
  align-items: center;
}
.checkbox-label {
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
.btn-cancel {
  background: #f1f1f1;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
}
.btn-save {
  background: #2ecc71;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}

/* ESTILOS ESPECÍFICOS PARA CATEGORIAS */
.add-cat-box {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}
.add-cat-box input[type='text'] {
  flex: 2;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.add-cat-box select {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.add-cat-box input[type='color'] {
  width: 40px;
  height: 38px;
  border: none;
  padding: 0;
  background: none;
  cursor: pointer;
}
.btn-mini-add {
  background: #2ecc71;
  color: white;
  border: none;
  width: 40px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 20px;
}

.cat-list {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 6px;
}
.cat-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.cat-info small {
  color: #999;
}
.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}
.btn-trash {
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0.5;
  transition: 0.2s;
}
.btn-trash:hover {
  opacity: 1;
  transform: scale(1.1);
}
</style>
