import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Chat from './pages/Chat';
import Pollution from './pages/Pollution';
import Irrigation from './pages/Irrigation';
import Emergency from './pages/Emergency';
import Strategic from './pages/Strategic';
import StrategicChat from './pages/StrategicChat';

// Required for i18n
import './i18n';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-background flex flex-col">
        <NavBar />
        <main className="flex-1 w-full">
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/pollution" element={<Pollution />} />
            <Route path="/irrigation" element={<Irrigation />} />
            <Route path="/emergency" element={<Emergency />} />
            <Route path="/strategic" element={<Strategic />} />
            <Route path="/strategic-chat" element={<StrategicChat />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
