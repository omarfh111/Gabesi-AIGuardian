import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Chat from './pages/Chat';
import Pollution from './pages/Pollution';
import Irrigation from './pages/Irrigation';

// Required for i18n
import './i18n';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background flex flex-col">
        <NavBar />
        <main className="flex-1 max-w-7xl mx-auto w-full">
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/pollution" element={<Pollution />} />
            <Route path="/irrigation" element={<Irrigation />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
