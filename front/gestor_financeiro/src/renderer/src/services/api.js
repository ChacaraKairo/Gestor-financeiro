import axios from 'axios';

// Cria uma conexão padrão apontando para o seu servidor Python
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000', // A URL onde o FastAPI está rodando
  timeout: 10000, // Tempo máximo de espera (10s)
  headers: {
    'Content-Type': 'application/json',
  }
});

export default api;