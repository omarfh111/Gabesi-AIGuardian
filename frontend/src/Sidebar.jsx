import React from 'react';
import { Activity, MessageSquare, ShieldAlert } from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  return (
    <div className="glass-panel" style={{ 
      width: '260px', 
      minHeight: '100%', 
      borderRadius: '0',
      borderLeft: 'none',
      borderTop: 'none',
      borderBottom: 'none',
      display: 'flex',
      flexDirection: 'column',
      padding: '2rem 1.5rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '3rem' }}>
        <ShieldAlert size={28} color="var(--accent-cyan)" />
        <h2 className="title-gradient" style={{ margin: 0 }}>Gabesi AI</h2>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <button 
          onClick={() => setActiveTab('dashboard')}
          style={{
            background: activeTab === 'dashboard' ? 'rgba(0, 240, 255, 0.1)' : 'transparent',
            border: 'none',
            color: activeTab === 'dashboard' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
            padding: '1rem',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            cursor: 'pointer',
            textAlign: 'left',
            fontFamily: 'Inter, sans-serif',
            fontSize: '1rem',
            fontWeight: 500,
            transition: 'all 0.2s',
          }}
        >
          <Activity size={20} />
          Dashboard
        </button>

        <button 
          onClick={() => setActiveTab('chat')}
          style={{
            background: activeTab === 'chat' ? 'rgba(0, 240, 255, 0.1)' : 'transparent',
            border: 'none',
            color: activeTab === 'chat' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
            padding: '1rem',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            cursor: 'pointer',
            textAlign: 'left',
            fontFamily: 'Inter, sans-serif',
            fontSize: '1rem',
            fontWeight: 500,
            transition: 'all 0.2s',
          }}
        >
          <MessageSquare size={20} />
          Agent Chat
        </button>
      </nav>

      <div style={{ marginTop: 'auto', paddingTop: '2rem', borderTop: '1px solid var(--glass-border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="status-dot active"></span>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>System Online</span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
