<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import api from '../services/api'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Pie } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip, Legend)

// --- ESTADOS ---
const resumo = ref({ receita: 0, despesa: 0, saldo: 0, pendente: 0 })
const transacoes = ref([])
const categorias = ref([])
const recorrencias = ref([])
const carregando = ref(false)

// Modais
const showModalTransacao = ref(false)
const showModalCategorias = ref(false)
const showModalRecorrencia = ref(false)

// Estado de Edição
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

// --- FUNÇÕES DE TRANSAÇÃO ---

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
    date: t.transaction_date, // Preenche o form com a data do banco
    category_id: t.category_id,
    is_fixed: t.is_fixed,
    is_paid: t.is_paid,
    payment_method: t.payment_method || 'Pix'
  }
  showModalTransacao.value = true
}

async function salvarTransacao() {
  if (!form.value.description || !form.value.amount || !form.value.category_id) {
    return alert('Preencha os campos obrigatórios!')
  }

  try {
    // CORREÇÃO AQUI: Montamos o payload manualmente para trocar 'date' por 'transaction_date'
    const payload = {
      description: form.value.description,
      amount: parseFloat(form.value.amount),
      transaction_date: form.value.date, // O Python exige este nome exato
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
    alert('Erro ao salvar transação.')
    console.error(error)
  }
}

async function excluirTransacao(id) {
  if (!confirm('Tem certeza que deseja excluir este lançamento?')) return
  try {
    await api.delete(`/transactions/${id}`)
    buscarDados()
  } catch (error) {
    alert('Erro ao excluir transação.')
  }
}

// --- OUTRAS FUNÇÕES ---
async function criarCategoria() {
  if (!novaCategoria.value.name) return alert('Digite um nome!')
  try {
    await api.post('/categories/', novaCategoria.value)
    const res = await api.get('/categories/')
    categorias.value = res.data
    novaCategoria.value.name = ''
  } catch (error) {
    alert('Erro ao criar categoria')
  }
}
async function excluirCategoria(id) {
  if (!confirm('Tem certeza?')) return
  try {
    await api.delete(`/categories/${id}`)
    const res = await api.get('/categories/')
    categorias.value = res.data
  } catch (error) {
    alert('Erro ao excluir.')
  }
}

async function abrirRecorrencias() {
  try {
    const res = await api.get('/recurring/')
    recorrencias.value = res.data
    showModalRecorrencia.value = true
  } catch (error) {
    alert('Erro ao buscar contas fixas.')
  }
}

async function criarRecorrencia() {
  if (!novaRecorrencia.value.description || !novaRecorrencia.value.estimated_amount)
    return alert('Preencha dados!')
  try {
    await api.post('/recurring/', novaRecorrencia.value)
    const res = await api.get('/recurring/')
    recorrencias.value = res.data
    novaRecorrencia.value.description = ''
    novaRecorrencia.value.estimated_amount = ''
  } catch (error) {
    alert('Erro ao criar modelo de conta fixa.')
  }
}

async function excluirRecorrencia(id) {
  if (!confirm('Parar de gerar esta conta automaticamente?')) return
  try {
    await api.delete(`/recurring/${id}`)
    const res = await api.get('/recurring/')
    recorrencias.value = res.data
  } catch (error) {
    alert('Erro ao excluir.')
  }
}

async function importarContasFixas() {
  const mesNome = meses.find((m) => m.v === filtros.value.mes).n
  if (!confirm(`Deseja gerar as contas fixas para ${mesNome}/${filtros.value.ano}?`)) return
  try {
    const res = await api.post(
      `/transactions/generate-fixed/${filtros.value.mes}/${filtros.value.ano}`
    )
    alert(res.data.message)
    buscarDados()
  } catch (error) {
    console.error(error)
    alert('Erro ao gerar contas fixas.')
  }
}

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
          ⚙️ Cats
        </button>
        <button class="btn-config" @click="abrirRecorrencias" title="Configurar Contas Fixas">
          📅 Fixas
        </button>
        <div class="separator"></div>
        <select v-model="filtros.mes">
          <option v-for="m in meses" :key="m.v" :value="m.v">{{ m.n }}</option>
        </select>
        <input type="number" v-model="filtros.ano" class="ano-input" />
        <button class="btn-import" @click="importarContasFixas" title="Gerar contas deste mês">
          📥 Importar Fixas
        </button>
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
      <div class="card pendente">
        <h3>A Pagar (Pendente)</h3>
        <p class="valor">{{ money(resumo.pendente) }}</p>
      </div>
    </div>

    <div class="main-content">
      <div class="section-table">
        <div class="section-header">
          <h2>Lançamentos</h2>
          <button class="btn-add" @click="abrirNovaTransacao">+ Novo Lançamento</button>
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
                <td>{{ t.description }}</td>
                <td>
                  <span class="badge" :style="{ backgroundColor: t.category?.color_hex }">{{
                    t.category?.name
                  }}</span>
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
                  <button class="btn-icon edit" @click="editarTransacao(t)" title="Editar">
                    ✏️
                  </button>
                  <button class="btn-icon trash" @click="excluirTransacao(t.id)" title="Excluir">
                    🗑️
                  </button>
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
        <h3>{{ transacaoEmEdicaoId ? 'Editar Transação' : 'Nova Transação' }}</h3>

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
          <input v-model="novaCategoria.name" type="text" placeholder="Nome" />
          <select v-model="novaCategoria.type">
            <option value="DESPESA">Despesa</option>
            <option value="RECEITA">Receita</option>
          </select>
          <input type="color" v-model="novaCategoria.color_hex" />
          <button @click="criarCategoria" class="btn-mini-add">+</button>
        </div>
        <div class="cat-list">
          <div v-for="cat in categorias" :key="cat.id" class="cat-item">
            <div class="cat-info">
              <span class="color-dot" :style="{ background: cat.color_hex }"></span>
              <strong>{{ cat.name }}</strong>
            </div>
            <button class="btn-trash" @click="excluirCategoria(cat.id)">🗑️</button>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showModalCategorias = false">Fechar</button>
        </div>
      </div>
    </div>

    <div v-if="showModalRecorrencia" class="modal-overlay">
      <div class="modal-content large-modal">
        <h3>Configurar Contas Fixas</h3>
        <p class="modal-desc">Cadastre aqui o que você paga todo mês.</p>
        <div class="add-cat-box">
          <input v-model="novaRecorrencia.description" type="text" placeholder="Ex: Aluguel..." />
          <input
            v-model="novaRecorrencia.estimated_amount"
            type="number"
            placeholder="Valor Estimado"
            style="width: 100px"
          />
          <select v-model="novaRecorrencia.category_id">
            <option value="" disabled>Categoria</option>
            <option v-for="cat in categorias" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
          <button @click="criarRecorrencia" class="btn-mini-add">+</button>
        </div>
        <div class="cat-list">
          <div v-for="item in recorrencias" :key="item.id" class="cat-item">
            <div class="cat-info">
              <strong>{{ item.description }}</strong>
              <span class="badge-value">{{ money(item.estimated_amount) }}</span>
            </div>
            <button class="btn-trash" @click="excluirRecorrencia(item.id)">🗑️</button>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showModalRecorrencia = false">Fechar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Estilos Base */
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
.btn-config {
  padding: 8px 12px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: #555;
  transition: 0.2s;
}
.btn-config:hover {
  background: #f5f5f5;
  color: #333;
}
.btn-import {
  padding: 8px 12px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  font-size: 13px;
}
.btn-import:hover {
  background: #2980b9;
}
.btn-refresh {
  padding: 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 1.2rem;
}
.kpi-container {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin-top: 10px;
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
}
.badge {
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
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
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
}
.btn-add:hover {
  background: #000;
}
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
  width: 550px;
}
.modal-desc {
  font-size: 13px;
  color: #666;
  margin-bottom: 20px;
  margin-top: -10px;
}
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
.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
}
.badge-value {
  font-size: 12px;
  color: #555;
  background: #e0e0e0;
  padding: 2px 6px;
  border-radius: 4px;
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
  color: red;
}
.empty-msg-small {
  text-align: center;
  color: #999;
  font-size: 13px;
  margin-top: 10px;
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
.btn-icon {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  margin-left: 5px;
  opacity: 0.7;
  transition: 0.2s;
}
.btn-icon:hover {
  opacity: 1;
  transform: scale(1.1);
}
.btn-icon.edit:hover {
  background-color: #f0f8ff;
  border-radius: 4px;
}
.btn-icon.trash:hover {
  background-color: #fff0f0;
  border-radius: 4px;
}
</style>
