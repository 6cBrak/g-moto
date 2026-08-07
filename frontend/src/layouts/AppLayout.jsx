import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useUiStore } from '../store/uiStore'
import { useResourceListAll } from '../hooks/useResource'

const ROLES_TOUS = ['admin', 'gerant', 'vendeur_caissier']
const ROLES_GESTION = ['admin', 'gerant']

const navGroups = [
  { type: 'link', to: '/', label: 'Tableau de bord', roles: ROLES_TOUS },
  {
    type: 'group',
    label: 'Stock',
    items: [
      { to: '/catalogue', label: 'Catalogue', roles: ROLES_GESTION },
      { to: '/stock/arrivages', label: 'Arrivages', roles: ROLES_GESTION },
      { to: '/stock/motos', label: 'Motos', roles: ROLES_TOUS },
      { to: '/stock/alertes', label: 'Alertes stock', roles: ROLES_GESTION },
      { to: '/stock/marge-arrivages', label: 'Marge par arrivage', roles: ROLES_GESTION },
    ],
  },
  {
    type: 'group',
    label: 'Facturation',
    items: [
      { to: '/clients', label: 'Clients', roles: ROLES_TOUS },
      { to: '/depots', label: 'Depots revendeurs', roles: ROLES_GESTION },
      { to: '/factures', label: 'Factures', roles: ROLES_TOUS },
    ],
  },
  {
    type: 'group',
    label: 'Caisse',
    items: [
      { to: '/caisse/session', label: 'Ouverture / fermeture caisse', roles: ROLES_TOUS },
      { to: '/caisse/versements', label: 'Versements', roles: ROLES_TOUS },
      { to: '/caisse/sorties', label: 'Sorties de caisse', roles: ROLES_TOUS },
      { to: '/caisse/journal', label: 'Journal de caisse', roles: ROLES_TOUS },
      { to: '/caisse/rapports', label: 'Rapports caisse', roles: ROLES_TOUS },
    ],
  },
  { type: 'link', to: '/depenses', label: 'Depenses', roles: ROLES_GESTION },
  {
    type: 'group',
    label: 'Apres-vente',
    items: [
      { to: '/apresvente/garanties', label: 'Garanties', roles: ROLES_GESTION },
      { to: '/apresvente/entretiens', label: 'Entretiens', roles: ROLES_GESTION },
    ],
  },
  {
    type: 'group',
    label: 'Administration',
    items: [
      { to: '/admin/agences', label: 'Agences', roles: ['admin'] },
      { to: '/admin/utilisateurs', label: 'Utilisateurs', roles: ['admin', 'gerant'] },
      { to: '/admin/comparatif-agences', label: 'Comparatif agences', roles: ['admin'] },
      { to: '/admin/journal-activite', label: 'Journal d\'activite', roles: ROLES_GESTION },
      { to: '/admin/parametrage', label: 'Parametrage', roles: ['admin'] },
    ],
  },
]

function groupeActif(pathname) {
  const groupe = navGroups.find((g) => g.type === 'group' && g.items.some((item) => item.to === pathname))
  return groupe?.label ?? null
}

export default function AppLayout() {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const agenceFiltre = useUiStore((state) => state.agenceFiltre)
  const setAgenceFiltre = useUiStore((state) => state.setAgenceFiltre)
  const { data: agences } = useResourceListAll('agences', {}, { enabled: user?.role === 'admin' })
  const location = useLocation()

  const [openGroups, setOpenGroups] = useState(() => {
    const actif = groupeActif(location.pathname)
    return actif ? new Set([actif]) : new Set()
  })
  const [sidebarOuverte, setSidebarOuverte] = useState(false)

  useEffect(() => {
    const actif = groupeActif(location.pathname)
    if (actif) {
      setOpenGroups((prev) => (prev.has(actif) ? prev : new Set(prev).add(actif)))
    }
  }, [location.pathname])

  useEffect(() => {
    setSidebarOuverte(false)
  }, [location.pathname])

  const toggleGroup = (label) => {
    setOpenGroups((prev) => {
      const next = new Set(prev)
      if (next.has(label)) next.delete(label)
      else next.add(label)
      return next
    })
  }

  const linkClass = ({ isActive }) =>
    `block px-4 py-2 text-sm ${isActive ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-800'}`

  const sousLinkClass = ({ isActive }) =>
    `block pl-7 pr-4 py-2 text-sm ${isActive ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-800'}`

  return (
    <div className="min-h-screen flex bg-slate-50">
      {sidebarOuverte && (
        <button
          type="button"
          aria-label="Fermer le menu"
          onClick={() => setSidebarOuverte(false)}
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 text-slate-200 flex flex-col shrink-0
          transform transition-transform duration-200 ease-in-out
          ${sidebarOuverte ? 'translate-x-0' : '-translate-x-full'}
          md:relative md:translate-x-0 md:z-auto`}
      >
        <div className="px-4 py-4 flex items-center justify-between border-b border-slate-800">
          <span className="text-lg font-semibold text-white">Gestion Motos</span>
          <button
            type="button"
            aria-label="Fermer le menu"
            onClick={() => setSidebarOuverte(false)}
            className="text-slate-400 hover:text-white text-xl leading-none md:hidden"
          >
            ×
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto py-2">
          {navGroups.map((entry) => {
            if (entry.type === 'link') {
              if (!entry.roles.includes(user?.role)) return null
              return (
                <NavLink key={entry.to} to={entry.to} end={entry.to === '/'} className={linkClass}>
                  {entry.label}
                </NavLink>
              )
            }

            const items = entry.items.filter((item) => item.roles.includes(user?.role))
            if (items.length === 0) return null
            const ouvert = openGroups.has(entry.label)

            return (
              <div key={entry.label}>
                <button
                  type="button"
                  onClick={() => toggleGroup(entry.label)}
                  className="w-full flex items-center justify-between px-4 py-2 text-xs font-medium text-slate-400 uppercase tracking-wide hover:text-slate-200"
                >
                  <span>{entry.label}</span>
                  <span className={`transition-transform ${ouvert ? 'rotate-90' : ''}`}>&rsaquo;</span>
                </button>
                {ouvert && items.map((item) => (
                  <NavLink key={item.to} to={item.to} className={sousLinkClass}>
                    {item.label}
                  </NavLink>
                ))}
              </div>
            )
          })}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b border-slate-200 px-3 sm:px-6 py-3 flex items-center justify-between gap-2">
          <div className="flex items-center gap-3 min-w-0">
            <button
              type="button"
              aria-label="Ouvrir le menu"
              onClick={() => setSidebarOuverte(true)}
              className="text-slate-600 hover:text-slate-900 md:hidden shrink-0"
            >
              <span className="block w-6 space-y-1">
                <span className="block h-0.5 bg-current" />
                <span className="block h-0.5 bg-current" />
                <span className="block h-0.5 bg-current" />
              </span>
            </button>
            <div className="text-sm text-slate-600 truncate">
              {user?.username} — <span className="font-medium">{user?.role}</span>
              {user?.agence_nom && <span> — {user.agence_nom}</span>}
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-4 shrink-0">
            {user?.role === 'admin' && (
              <select
                className="border border-slate-300 rounded px-1.5 sm:px-2 py-1 text-xs sm:text-sm max-w-[7.5rem] sm:max-w-none"
                value={agenceFiltre ?? ''}
                onChange={(e) => setAgenceFiltre(e.target.value || null)}
              >
                <option value="">Toutes les agences</option>
                {agences?.map((agence) => (
                  <option key={agence.id} value={agence.id}>{agence.nom}</option>
                ))}
              </select>
            )}
            <button onClick={logout} className="text-sm text-slate-600 hover:text-slate-900 underline whitespace-nowrap">
              Deconnexion
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-3 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
