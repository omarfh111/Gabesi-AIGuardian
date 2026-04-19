import React, { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Globe, ShieldAlert } from 'lucide-react';

const NavBar = () => {
  const { t, i18n } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
  };

  useEffect(() => {
    document.documentElement.dir = i18n.language === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);

  const navLinks = [
    { to: '/', label: t('nav.chat') },
    { to: '/pollution', label: t('nav.pollution') },
    { to: '/irrigation', label: t('nav.irrigation') },
    { to: '/strategic', label: t('nav.strategic') },
    { to: '/strategic-chat', label: t('nav.strategic_chat') },
    { to: '/community-map', label: t('nav.community_map', 'Community Map') },
    { to: '/emergency', label: t('nav.emergency'), isEmergency: true },
    { to: '/medical', label: t('nav.medical', 'Medical Triage') },
    { to: '/energy', label: t('nav.energy', 'Energy Advisor') },
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white/95 px-4 py-2 shadow-sm backdrop-blur">
      <div className="mx-auto flex max-w-[1800px] items-center justify-between gap-4">
        <div className="flex min-w-[240px] items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-xl border border-sky-100 bg-white shadow-sm">
            <img src="/logo.png" alt="Gabesi AIGuardian logo" className="h-full w-full object-cover" />
          </div>
          <div>
            <h1 className="text-lg font-bold leading-none text-slate-900">{t('appName')}</h1>
            <p className="text-[10px] uppercase tracking-wide text-slate-500">Environmental Intelligence Platform</p>
          </div>
        </div>

        <div className="hidden min-w-0 flex-1 lg:block">
          <div className="flex items-center gap-1 overflow-x-auto rounded-xl border border-gray-200 bg-slate-50 p-1">
            {navLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `whitespace-nowrap rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wide transition ${
                    isActive
                      ? link.isEmergency
                        ? 'bg-red-500 text-white'
                        : 'bg-sky-600 text-white'
                      : link.isEmergency
                      ? 'text-red-600 hover:bg-red-50'
                      : 'text-slate-600 hover:bg-white hover:text-sky-700'
                  }`
                }
              >
                <span className="flex items-center gap-1.5">
                  {link.isEmergency ? <ShieldAlert className="h-3.5 w-3.5" /> : null}
                  {link.label}
                </span>
              </NavLink>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 lg:flex">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-[10px] font-semibold uppercase tracking-wide text-emerald-700">System Active</span>
          </div>

          <div className="flex items-center gap-1 rounded-lg border border-gray-200 bg-slate-50 p-1">
            <Globe className="mx-1 h-4 w-4 text-slate-500" />
            {['en', 'fr', 'ar'].map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => changeLanguage(lang)}
                className={`h-7 rounded px-2 text-[10px] font-semibold uppercase transition ${
                  i18n.language === lang ? 'bg-sky-600 text-white' : 'text-slate-600 hover:bg-white hover:text-sky-700'
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
