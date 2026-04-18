import { useState } from 'react';
import Sidebar from './Sidebar';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-content">
        {activeTab === 'dashboard' ? <Dashboard /> : <Chat />}
      </main>
    </div>
  );
}

export default App;
