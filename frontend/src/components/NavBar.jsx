import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Globe, ShieldAlert } from 'lucide-react';

const NavBar = () => {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    document.documentElement.dir = lng === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = lng;
  };

  const navLinks = [
    { to: '/', label: t('nav.chat') },
    { to: '/pollution', label: t('nav.pollution') },
    { to: '/irrigation', label: t('nav.irrigation') },
    { to: '/strategic', label: t('nav.strategic') },
    { to: '/strategic-chat', label: t('nav.strategic_chat') },
    { to: '/emergency', label: t('nav.emergency'), isEmergency: true },
  ];

  return (
    <nav className="sticky top-0 z-50 h-16 glass border-b border-border px-6 flex items-center justify-between shadow-2xl">
      {/* Left: Logo & Title (Friend's Style) */}
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl bg-gradient-to-br from-accent to-purple shadow-lg shadow-accent/20">
          🌍
        </div>
        <div>
          <h1 className="text-lg font-black tracking-tighter leading-none bg-gradient-to-r from-accent to-purple bg-clip-text text-transparent uppercase">
            {t('appName')}
          </h1>
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest mt-1">
            Environmental Intelligence Platform
          </p>
        </div>
      </div>

      {/* Center: Navigation Links */}
      <div className="hidden md:flex items-center gap-1 p-1 bg-primary/40 rounded-xl border border-border">
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all duration-300 ${
                isActive 
                  ? link.isEmergency 
                    ? 'bg-danger text-white shadow-lg shadow-danger/30' 
                    : 'bg-accent/10 text-accent shadow-inner'
                  : link.isEmergency
                    ? 'text-danger hover:bg-danger/10'
                    : 'text-text-secondary hover:text-accent hover:bg-white/5'
              }`
            }
          >
            <div className="flex items-center gap-2">
              {link.isEmergency && <ShieldAlert className="w-3 h-3 animate-pulse" />}
              {link.label}
            </div>
          </NavLink>
        ))}
      </div>

      {/* Right: Status & Language */}
      <div className="flex items-center gap-6">
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-[10px] font-black text-green-500 uppercase tracking-widest">System Active</span>
        </div>

        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-text-muted" />
          <div className="flex gap-1 p-1 bg-primary/40 rounded-lg border border-border">
            {['en', 'fr', 'ar'].map((lang) => (
              <button
                key={lang}
                onClick={() => changeLanguage(lang)}
                className={`w-7 h-7 flex items-center justify-center text-[10px] font-black uppercase rounded transition-all ${
                  i18n.language === lang 
                    ? 'bg-accent text-primary' 
                    : 'text-text-muted hover:text-text-secondary hover:bg-white/5'
                }`}
              >
                {lang}
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavBar;
