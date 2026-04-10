import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import CustomerSearch from "./pages/CustomerSearch";
import CustomerDetail from "./pages/CustomerDetail";
import PromptEditor from "./pages/PromptEditor";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <h1 className="logo">Nasta AS</h1>
          <span className="logo-sub">Kundeservice PoC</span>
          <nav className="header-nav">
            <Link to="/">Kundesøk</Link>
            <Link to="/prompt">AI Prompt</Link>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<CustomerSearch />} />
            <Route path="/kunde" element={<CustomerDetail />} />
            <Route path="/prompt" element={<PromptEditor />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
