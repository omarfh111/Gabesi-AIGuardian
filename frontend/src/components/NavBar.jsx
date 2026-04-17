import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';

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
  ];

  return (
    <nav className="bg-primary text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold">{t('appName')}</span>
        </div>

        <div className="flex gap-6">
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `text-sm font-medium hover:text-accent transition-colors ${
                  isActive ? 'text-accent border-b-2 border-accent' : ''
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4" />
          <div className="flex gap-2">
            {['en', 'fr', 'ar'].map((lang) => (
              <button
                key={lang}
                onClick={() => changeLanguage(lang)}
                className={`text-xs uppercase px-2 py-1 rounded hover:bg-secondary transition-colors ${
                  i18n.language === lang ? 'bg-secondary font-bold' : ''
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
