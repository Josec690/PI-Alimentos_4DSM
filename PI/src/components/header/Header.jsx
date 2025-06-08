import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FaUserCircle } from 'react-icons/fa';
import './Header.css';
import logoBranca from '../../assets/Logo-branca.png';
import logoPreta from '../../assets/Logo-preta.png';

const Header = () => {
  const location = useLocation();
  const isHome = location.pathname === '/';

  // Verifica se o usuário está logado (ajuste conforme sua lógica real)
  const isLoggedIn = !!localStorage.getItem('token');

  return (
    <header className={`header ${isHome ? 'dark' : 'light'}`}>
      <div className="logo">
        <Link to="/">
          <img src={isHome ? logoBranca : logoPreta} alt="Logo" />
        </Link>
      </div>

      <nav className="nav">
        <Link to="/sobre">Sobre Nós</Link>
        <Link to="/receitas">Receitas</Link>
        <Link to="/Doacao">Doe</Link>

        {isLoggedIn ? (
          <Link to="/usuario" className="perfil-icon" title="Perfil">
            <FaUserCircle size={28} />
          </Link>
        ) : (
          <>
            <Link to="/cadastro">Cadastrar</Link>
            <Link to="/login">Entrar</Link>
          </>
        )}
      </nav>
    </header>
  );
};

export default Header;
