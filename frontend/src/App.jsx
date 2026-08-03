import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ProtectedRoute from './routes/ProtectedRoute'
import AppLayout from './layouts/AppLayout'

import CataloguePage from './pages/catalogue/CataloguePage'
import ArrivagesPage from './pages/stock/ArrivagesPage'
import MotosPage from './pages/stock/MotosPage'
import StockAlertesPage from './pages/stock/StockAlertesPage'
import MargeArrivagesPage from './pages/stock/MargeArrivagesPage'
import ClientsPage from './pages/facturation/ClientsPage'
import DepotsPage from './pages/facturation/DepotsPage'
import FacturesListPage from './pages/facturation/FacturesListPage'
import FactureCreatePage from './pages/facturation/FactureCreatePage'
import FactureDetailPage from './pages/facturation/FactureDetailPage'
import VersementsPage from './pages/caisse/VersementsPage'
import JournalCaissePage from './pages/caisse/JournalCaissePage'
import RapportsCaissePage from './pages/caisse/RapportsCaissePage'
import SessionCaissePage from './pages/caisse/SessionCaissePage'
import SortiesCaissePage from './pages/caisse/SortiesCaissePage'
import DepensesPage from './pages/DepensesPage'
import GarantiesPage from './pages/apresvente/GarantiesPage'
import EntretiensPage from './pages/apresvente/EntretiensPage'
import AgencesPage from './pages/admin/AgencesPage'
import UtilisateursPage from './pages/admin/UtilisateursPage'
import ComparatifAgencesPage from './pages/admin/ComparatifAgencesPage'
import ParametragePage from './pages/admin/ParametragePage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/catalogue" element={<CataloguePage />} />
            <Route path="/stock/arrivages" element={<ArrivagesPage />} />
            <Route path="/stock/motos" element={<MotosPage />} />
            <Route path="/stock/alertes" element={<StockAlertesPage />} />
            <Route path="/stock/marge-arrivages" element={<MargeArrivagesPage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/depots" element={<DepotsPage />} />
            <Route path="/factures" element={<FacturesListPage />} />
            <Route path="/factures/nouvelle" element={<FactureCreatePage />} />
            <Route path="/factures/:id" element={<FactureDetailPage />} />
            <Route path="/caisse/session" element={<SessionCaissePage />} />
            <Route path="/caisse/versements" element={<VersementsPage />} />
            <Route path="/caisse/sorties" element={<SortiesCaissePage />} />
            <Route path="/caisse/journal" element={<JournalCaissePage />} />
            <Route path="/caisse/rapports" element={<RapportsCaissePage />} />
            <Route path="/depenses" element={<DepensesPage />} />
            <Route path="/apresvente/garanties" element={<GarantiesPage />} />
            <Route path="/apresvente/entretiens" element={<EntretiensPage />} />
            <Route path="/admin/agences" element={<AgencesPage />} />
            <Route path="/admin/utilisateurs" element={<UtilisateursPage />} />
            <Route path="/admin/comparatif-agences" element={<ComparatifAgencesPage />} />
            <Route path="/admin/parametrage" element={<ParametragePage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
