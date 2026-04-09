import { BrowserRouter, Routes, Route } from "react-router-dom";
import CustomerSearch from "./pages/CustomerSearch";
import CustomerDetail from "./pages/CustomerDetail";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <h1 className="logo">Nasta AS</h1>
          <span className="logo-sub">Kundeservice PoC</span>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<CustomerSearch />} />
            <Route path="/kunde" element={<CustomerDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
