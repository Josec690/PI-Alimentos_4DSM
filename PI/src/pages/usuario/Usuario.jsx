import React, { useEffect, useState } from 'react';
import Header from '../../components/header/Header';
import Footer from '../../components/footer/Footer';
import { useNavigate } from 'react-router-dom';
import './Usuario.css'; // importante importar o CSS atualizado

function Usuario() {
  const navigate = useNavigate();
  const [usuario, setUsuario] = useState({ nome: '', email: '' });
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetch('http://localhost:5000/perfil', {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Falha ao obter perfil');
        return res.json();
      })
      .then(data => {
        setUsuario({
          nome: data.usuario.nome,
          email: data.usuario.email
        });
      })
      .catch(err => setErro(err.message))
      .finally(() => setLoading(false));
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  if (loading) return <p className="estado-feedback">Carregando...</p>;
  if (erro) return <p className="estado-feedback erro">Erro: {erro}</p>;

  return (
    <>
      <Header />
      <div className="user-container">
        <div className="avatar">
          <span>{usuario.nome.charAt(0).toUpperCase()}</span>
        </div>
        <h2>Minha Conta</h2>
        <div className="user-info">
          <p><strong>Nome:</strong> {usuario.nome}</p>
          <p><strong>Email:</strong> {usuario.email}</p>
        </div>
        <div className="alterar-senha-container">
          <button className="alterar-senha-botao" onClick={() => navigate('/alterar-senha')}>
            Alterar Senha
          </button>
          <button className="sair-botao" onClick={handleLogout}>
            Sair
          </button>
        </div>
      </div>
      <Footer />
    </>
  );
}

export default Usuario;
