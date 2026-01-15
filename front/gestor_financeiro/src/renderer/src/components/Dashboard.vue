<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../services/api'

// Importando nossos novos componentes
import KpiCards from './KpiCards.vue'
import DashboardCharts from './DashboardCharts.vue'
import TransactionTable from './TransactionTable.vue'

// --- ESTADOS ---
const resumo = ref({ receita: 0, despesa: 0, saldo: 0, pendente: 0 })
const historico = ref([])
const transacoes = ref([])
const categorias = ref([])
const recorrencias = ref([])
const carregando = ref(false)

// Modais (Mantidos aqui por enquanto para simplificar a lógica de formulário)
const showModalTransacao = ref(false)
const showModalCategorias = ref(false)
const showModalRecorrencia = ref(false)
const transacaoEmEdicaoId = ref(null)

// Filtros
const dataAtual = new Date()
const filtros = ref({
  mes: dataAtual.getMonth() + 1,
  ano: dataAtual.getFullYear()
})

// Forms
const form = ref({
  description: '',
  amount: '',
  date: new Date().toISOString().substr(0, 10),
  category_id: '',
  is_fixed: false,
  is_paid: true,
  payment_method: 'Pix'
})
const novaCategoria = ref({ name: '', color_hex: '#333333', type: 'DESPESA' })
const novaRecorrencia = ref({
  description: '',
  estimated_amount: '',
  category_id: '',
  active: true
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

// --- FUNÇÕES ---
async function buscarDados() {
  carregando.value = true
  try {
    const params = { month: filtros.value.mes, year: filtros.value.ano }
    const [resResumo, resTrans, resCats, resHist] = await Promise.all([
      api.get('/dashboard/summary', { params }),
      api.get('/transactions/', { params }),
      api.get('/categories/'),
      api.get('/dashboard/history', { params: { year: filtros.value.ano } })
    ])
    resumo.value = resResumo.data
    transacoes.value = resTrans.data
    categorias.value = resCats.data
    historico.value = resHist.data
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
    alert('Erro ao conectar com o servidor.')
  } finally {
    carregando.value = false
  }
}

// --- CRUD TRANSAÇÕES ---
function abrirNovaTransacao() {
  transacaoEmEdicaoId.value = null
  form.value = {
    description: '',
    amount: '',
    date: new Date().toISOString().substr(0, 10),
    category_id: '',
    is_fixed: false,
    is_paid: true,
    payment_method: 'Pix'
  }
  showModalTransacao.value = true
}

function editarTransacao(t) {
  transacaoEmEdicaoId.value = t.id
  form.value = {
    description: t.description,
    amount: t.amount,
    date: t.transaction_date,
    category_id: t.category_id,
    is_fixed: t.is_fixed,
    is_paid: t.is_paid,
    payment_method: t.payment_method || 'Pix'
  }
  showModalTransacao.value = true
}

async function salvarTransacao() {
  if (!form.value.description || !form.value.amount || !form.value.category_id)
    return alert('Preencha os campos!')
  try {
    const payload = {
      description: form.value.description,
      amount: parseFloat(form.value.amount),
      transaction_date: form.value.date,
      category_id: form.value.category_id,
      is_fixed: form.value.is_fixed,
      is_paid: form.value.is_paid,
      payment_method: form.value.payment_method
    }
    if (transacaoEmEdicaoId.value) {
      await api.put(`/transactions/${transacaoEmEdicaoId.value}`, payload)
    } else {
      await api.post('/transactions/', payload)
    }
    showModalTransacao.value = false
    buscarDados()
  } catch (error) {
    alert('Erro ao salvar.')
  }
}

async function excluirTransacao(id) {
  if (!confirm('Excluir?')) return
  try {
    await api.delete(`/transactions/${id}`)
    buscarDados()
  } catch {
    alert('Erro ao excluir.')
  }
}

// --- OUTRAS FUNÇÕES ---
async function criarCategoria() {
  try {
    await api.post('/categories/', novaCategoria.value)
    const res = await api.get('/categories/')
    categorias.value = res.data
    novaCategoria.value.name = ''
  } catch {
    alert('Erro')
  }
}
async function excluirCategoria(id) {
  if (!confirm('Excluir?')) return
  try {
    await api.delete(`/categories/${id}`)
    const res = await api.get('/categories/')
    categorias.value = res.data
  } catch {
    alert('Erro')
  }
}
async function abrirRecorrencias() {
  try {
    const res = await api.get('/recurring/')
    recorrencias.value = res.data
    showModalRecorrencia.value = true
  } catch {
    alert('Erro')
  }
}
async function criarRecorrencia() {
  try {
    await api.post('/recurring/', novaRecorrencia.value)
    const res = await api.get('/recurring/')
    recorrencias.value = res.data
    novaRecorrencia.value.description = ''
    novaRecorrencia.value.estimated_amount = ''
  } catch {
    alert('Erro')
  }
}
async function excluirRecorrencia(id) {
  if (!confirm('Parar recorrência?')) return
  try {
    await api.delete(`/recurring/${id}`)
    const res = await api.get('/recurring/')
    recorrencias.value = res.data
  } catch {
    alert('Erro')
  }
}
async function importarContasFixas() {
  if (!confirm(`Gerar contas?`)) return
  try {
    const res = await api.post(
      `/transactions/generate-fixed/${filtros.value.mes}/${filtros.value.ano}`
    )
    alert(res.data.message)
    buscarDados()
  } catch {
    alert('Erro')
  }
}
async function exportarRelatorio() {
  try {
    const response = await api.get('/transactions/export', { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `relatorio_${filtros.value.ano}.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch {
    alert('Erro ao baixar.')
  }
}

const money = (val) => Number(val).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const formatDate = (dateString) =>
  new Date(dateString).toLocaleDateString('pt-BR', { timeZone: 'UTC' })

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
        <button class="btn-config" @click="showModalCategorias = true">⚙️ Cats</button>
        <button class="btn-config" @click="abrirRecorrencias">📅 Fixas</button>
        <div class="separator"></div>
        <select v-model="filtros.mes">
          <option v-for="m in meses" :key="m.v" :value="m.v">{{ m.n }}</option>
        </select>
        <input type="number" v-model="filtros.ano" class="ano-input" />
        <button class="btn-import" @click="importarContasFixas">📥 Importar</button>
        <button class="btn-export" @click="exportarRelatorio">📤 Excel</button>
        <button class="btn-refresh" @click="buscarDados">🔄</button>
      </div>
    </header>

    <KpiCards :resumo="resumo" :money="money" />

    <div class="main-content">
      <TransactionTable
        :transacoes="transacoes"
        :money="money"
        :formatDate="formatDate"
        @novo="abrirNovaTransacao"
        @editar="editarTransacao"
        @excluir="excluirTransacao"
      />

      <DashboardCharts :transacoes="transacoes" :historico="historico" :meses="meses" />
    </div>

    <div v-if="showModalTransacao" class="modal-overlay">
      <div class="modal-content">
        <h3>{{ transacaoEmEdicaoId ? 'Editar' : 'Nova' }} Transação</h3>
        <div class="form-group"><label>Descrição</label><input v-model="form.description" /></div>
        <div class="form-row">
          <div class="form-group">
            <label>Valor</label><input v-model="form.amount" type="number" step="0.01" />
          </div>
          <div class="form-group"><label>Data</label><input v-model="form.date" type="date" /></div>
        </div>
        <div class="form-group">
          <label>Categoria</label
          ><select v-model="form.category_id">
            <option v-for="c in categorias" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div class="form-row checkbox-row">
          <label><input type="checkbox" v-model="form.is_paid" /> Pago?</label
          ><label><input type="checkbox" v-model="form.is_fixed" /> Fixo?</label>
        </div>
        <div class="modal-actions">
          <button @click="showModalTransacao = false">Cancelar</button
          ><button class="btn-save" @click="salvarTransacao">Salvar</button>
        </div>
      </div>
    </div>

    <div v-if="showModalCategorias" class="modal-overlay">
      <div class="modal-content large-modal">
        <h3>Categorias</h3>
        <div class="add-cat-box">
          <input v-model="novaCategoria.name" /><select v-model="novaCategoria.type">
            <option value="DESPESA">Despesa</option>
            <option value="RECEITA">Receita</option></select
          ><input type="color" v-model="novaCategoria.color_hex" /><button
            @click="criarCategoria"
            class="btn-mini-add"
          >
            +
          </button>
        </div>
        <div class="cat-list">
          <div v-for="c in categorias" :key="c.id" class="cat-item">
            <span class="color-dot" :style="{ background: c.color_hex }"></span>{{ c.name }}
            <button class="btn-icon trash" @click="excluirCategoria(c.id)">🗑️</button>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="showModalCategorias = false">Fechar</button>
        </div>
      </div>
    </div>

    <div v-if="showModalRecorrencia" class="modal-overlay">
      <div class="modal-content large-modal">
        <h3>Contas Fixas</h3>
        <div class="add-cat-box">
          <input v-model="novaRecorrencia.description" placeholder="Aluguel" /><input
            v-model="novaRecorrencia.estimated_amount"
            type="number"
            placeholder="Valor"
          /><select v-model="novaRecorrencia.category_id">
            <option v-for="c in categorias" :value="c.id">{{ c.name }}</option></select
          ><button @click="criarRecorrencia" class="btn-mini-add">+</button>
        </div>
        <div class="cat-list">
          <div v-for="r in recorrencias" :key="r.id" class="cat-item">
            {{ r.description }} ({{ money(r.estimated_amount) }})
            <button class="btn-icon trash" @click="excluirRecorrencia(r.id)">🗑️</button>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="showModalRecorrencia = false">Fechar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Estilos Layout Principal */
.dashboard {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-shrink: 0;
}
.subtitle {
  color: #666;
  margin: 0;
  font-size: 14px;
}
.filtros {
  display: flex;
  align-items: center;
  gap: 8px;
}
.filtros select,
.filtros input {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
}
.separator {
  width: 1px;
  height: 30px;
  background: #ddd;
  margin: 0 10px;
}
.btn-config,
.btn-import,
.btn-export,
.btn-refresh {
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: 0.2s;
  -webkit-app-region: no-drag;
}
.btn-config {
  background: #fff;
  border: 1px solid #ccc;
  color: #555;
}
.btn-import {
  background: #3498db;
  color: white;
  border: none;
}
.btn-export {
  background: #27ae60;
  color: white;
  border: none;
}
.btn-refresh {
  border: none;
  background: transparent;
  font-size: 1.2rem;
}

.main-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

/* Modais Estilos */
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
  padding: 20px;
  border-radius: 10px;
  width: 350px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  -webkit-app-region: no-drag;
}
.modal-content.large-modal {
  width: 500px;
}
.form-group {
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
}
.form-group label {
  font-size: 12px;
  font-weight: 600;
}
.form-group input,
.form-group select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 5px;
}
.form-row {
  display: flex;
  gap: 10px;
}
.form-row .form-group {
  flex: 1;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
.btn-save {
  background: #2ecc71;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 5px;
  font-weight: bold;
}
.btn-cancel {
  background: #f1f1f1;
  border: none;
  padding: 8px 15px;
  border-radius: 5px;
  cursor: pointer;
}
.add-cat-box {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}
.add-cat-box input,
.add-cat-box select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  flex: 1;
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
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cat-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 6px;
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
}

/* FIXES */
input,
select,
textarea,
button,
.modal-content {
  -webkit-app-region: no-drag !important;
  user-select: text !important;
  cursor: auto !important;
}
</style>
