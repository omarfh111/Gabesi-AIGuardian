import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import LoadingScreen from './components/LoadingScreen';
import Chat from './pages/Chat';
import Pollution from './pages/Pollution';
import Irrigation from './pages/Irrigation';
import Emergency from './pages/Emergency';
import Strategic from './pages/Strategic';
import StrategicChat from './pages/StrategicChat';
import CommunityMap from './pages/CommunityMap';
import Medical from './pages/Medical';
import Energy from './pages/Energy';

// Required for i18n
import './i18n';

function App() {
  const [showLoader, setShowLoader] = useState(() => {
    return !sessionStorage.getItem('gabesi_loaded');
  });

  const handleComplete = () => {
    sessionStorage.setItem('gabesi_loaded', 'true');
    setShowLoader(false);
  };

  if (showLoader) {
    return <LoadingScreen onComplete={handleComplete} />;
  }

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
            <Route path="/community-map" element={<CommunityMap />} />
            <Route path="/medical" element={<Medical />} />
            <Route path="/energy" element={<Energy />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
