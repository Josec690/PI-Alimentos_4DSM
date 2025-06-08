import './App.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Cadastro from './pages/cadastro/Cadastro'
import Home from './pages/home/Home'
import Sobre from './pages/sobre/Sobre'
import Login from './pages/login/Login'
import Receitas from './pages/receitas/Receitas'
import Carnes from './pages/carnes/Carnes'
import Aves from './pages/aves/Aves'
import Sobremesas from './pages/sobremesas/Sobremesas'
import Peixes from './pages/peixes/Peixes'
import MudarSenha from './pages/senha/MudarSenha'
import Doacao from './pages/doação/Doacao'
import Usuario from './pages/usuario/Usuario'
import Bolo from './pages/sobremesas/Bolo'
import EmailSenha from './pages/senha/EmailSenha'
import Panqueca from './pages/carnes/Panqueca'
import Pave from './pages/sobremesas/Pave'
import SorveteMorango from './pages/sobremesas/SorveteMorango'
import TortaLimao from './pages/sobremesas/TortaLimao'
import CriarReceita from './pages/criarReceita/CriarReceita'

function App() {
  return (
    <>
      <BrowserRouter>
        <Routes>
          <Route path='Cadastro' element={<Cadastro />} />
          <Route path='/' element={<Home />} />
          <Route path='Sobre' element={<Sobre />} />
          <Route path='Login' element={<Login />} />
          <Route path='Receitas' element={<Receitas />} />
          <Route path='Carnes' element={<Carnes />} />
          <Route path='Aves' element={<Aves />} />
          <Route path='Sobremesas' element={<Sobremesas />} />
          <Route path='Peixes' element={<Peixes />} />
          <Route path='MudarSenha' element={<MudarSenha />} />
          <Route path='Doacao'element={<Doacao/>} />
          <Route path='Usuario'element={<Usuario/>} />
          <Route path='Bolo'element={<Bolo/>} />
          <Route path='EmailSenha'element={<EmailSenha/>} />
          <Route path='Panqueca'element={<Panqueca/>} />
          <Route path='Pave'element={<Pave/>} />
          <Route path='SorveteMorango'element={<SorveteMorango/>} />
          <Route path='TortaLimao'element={<TortaLimao/>} />
          <Route path='CriarReceita' element={<CriarReceita />} />
        </Routes>
      </BrowserRouter>
    </>
  )
}

export default App
