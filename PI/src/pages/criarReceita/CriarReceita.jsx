import React, { useState, useEffect } from 'react';
import './CriarReceita.css';
import Header from '../../components/header/Header';
import Footer from '../../components/footer/Footer';

function CriarReceita() {
  // Estados para criação
  const [titulo, setTitulo] = useState('');
  const [ingredientes, setIngredientes] = useState('');
  const [modoPreparo, setModoPreparo] = useState('');
  const [categoria, setCategoria] = useState('Sobremesa');
  const [descricao, setDescricao] = useState('');
  const [tempoPreparo, setTempoPreparo] = useState('');
  const [porcoes, setPorcoes] = useState('');
  const [dificuldade, setDificuldade] = useState('média');

  const [mensagem, setMensagem] = useState('');

  // Estados para listagem
  const [receitas, setReceitas] = useState([]);
  const [busca, setBusca] = useState('');
  const [loading, setLoading] = useState(false);
  const [erroLista, setErroLista] = useState('');

  // Função para buscar receitas do backend
  const buscarReceitas = async (filtroBusca = '') => {
    setLoading(true);
    setErroLista('');
    try {
      let url = 'http://localhost:5000/receitas';
      if (filtroBusca) {
        url += `?busca=${encodeURIComponent(filtroBusca)}`;
      }
      const resposta = await fetch(url);
      const dados = await resposta.json();
      if (resposta.ok) {
        setReceitas(dados.receitas);
      } else {
        setErroLista(dados.erro || 'Erro ao carregar receitas.');
      }
    } catch {
      setErroLista('Erro de conexão com o servidor.');
    }
    setLoading(false);
  };

  // Busca inicial e toda vez que o filtro "busca" muda (com debounce)
  useEffect(() => {
    // Pequeno debounce manual para não fazer requisição a cada tecla rapidamente
    const timer = setTimeout(() => {
      buscarReceitas(busca);
    }, 500);
    return () => clearTimeout(timer);
  }, [busca]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const token = localStorage.getItem('token');
    if (!token) {
      setMensagem('Você precisa estar logado para enviar uma receita.');
      return;
    }

    const novaReceita = {
      titulo,
      ingredientes,
      modo_preparo: modoPreparo,
      categoria,
      descricao,
      tempo_preparo: tempoPreparo ? tempoPreparo : undefined,
      porcoes: porcoes ? porcoes : undefined,
      dificuldade
    };

    try {
      const resposta = await fetch('http://localhost:5000/receitas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(novaReceita)
      });

      const dados = await resposta.json();

      if (resposta.ok) {
        setMensagem('Receita enviada com sucesso!');
        // Resetar campos
        setTitulo('');
        setIngredientes('');
        setModoPreparo('');
        setCategoria('Sobremesa');
        setDescricao('');
        setTempoPreparo('');
        setPorcoes('');
        setDificuldade('média');

        // Atualizar lista para mostrar receita nova
        buscarReceitas(busca);
      } else {
        setMensagem(dados.erro || 'Erro ao enviar receita.');
      }
    } catch {
      setMensagem('Erro de conexão com o servidor.');
    }
  };

  return (
    <>
      <Header />
      <div className="form-receita-container">
        <h2>Enviar Nova Receita</h2>
        <form className="form-receita" onSubmit={handleSubmit}>
          {/* Formulário criação */}
          <label>
            Título da Receita:
            <input
              type="text"
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
              required
            />
          </label>

          <label>
            Ingredientes:
            <textarea
              value={ingredientes}
              onChange={(e) => setIngredientes(e.target.value)}
              rows="5"
              required
            />
          </label>

          <label>
            Modo de Preparo:
            <textarea
              value={modoPreparo}
              onChange={(e) => setModoPreparo(e.target.value)}
              rows="5"
              required
            />
          </label>

          <label>
            Categoria:
            <select
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
              required
            >
              <option value="Sobremesa">Sobremesa</option>
              <option value="Carnes">Carnes</option>
              <option value="Peixes">Peixes</option>
              <option value="Aves">Aves</option>
              <option value="Saladas">Saladas</option>
            </select>
          </label>

          {/* Campos opcionais */}
          <label>
            Descrição:
            <textarea
              value={descricao}
              onChange={(e) => setDescricao(e.target.value)}
              rows="3"
            />
          </label>

          <label>
            Tempo de Preparo (minutos):
            <input
              type="number"
              min="0"
              value={tempoPreparo}
              onChange={(e) => setTempoPreparo(e.target.value)}
            />
          </label>

          <label>
            Porções:
            <input
              type="number"
              min="1"
              value={porcoes}
              onChange={(e) => setPorcoes(e.target.value)}
            />
          </label>

          <label>
            Dificuldade:
            <select
              value={dificuldade}
              onChange={(e) => setDificuldade(e.target.value)}
            >
              <option value="fácil">Fácil</option>
              <option value="média">Média</option>
              <option value="difícil">Difícil</option>
            </select>
          </label>

          <button type="submit">Enviar Receita</button>
          {mensagem && <p className="mensagem">{mensagem}</p>}
        </form>

        {/* Área de listagem */}
        <div className="lista-receitas">
          <h2>Receitas Cadastradas</h2>

          <input
            type="text"
            placeholder="Buscar receitas por título, ingrediente ou descrição"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            className="input-busca"
          />

          {loading && <p>Carregando receitas...</p>}
          {erroLista && <p className="erro-lista">{erroLista}</p>}

          {!loading && receitas.length === 0 && <p>Nenhuma receita encontrada.</p>}

          <ul>
            {receitas.map((r) => (
              <li key={r._id} className="item-receita">
                <h3>{r.titulo}</h3>
                <p><strong>Categoria:</strong> {r.categoria}</p>
                {r.descricao && <p><em>{r.descricao}</em></p>}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <Footer />
    </>
  );
}

export default CriarReceita;
