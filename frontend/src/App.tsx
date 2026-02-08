import { Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import DiscourseBrowser from './pages/DiscourseBrowser'
import SampleDetail from './pages/SampleDetail'
import AnalysisInsights from './pages/AnalysisInsights'
import ResearchWorkspace from './pages/ResearchWorkspace'
import CollectionDashboard from './pages/CollectionDashboard'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Register from './pages/Register'

function App() {
  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1f2937',
            color: '#f9fafb',
          },
          success: {
            iconTheme: {
              primary: '#22c55e',
              secondary: '#f9fafb',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#f9fafb',
            },
          },
        }}
      />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/samples" element={<DiscourseBrowser />} />
          <Route path="/samples/:id" element={<SampleDetail />} />
          <Route path="/analysis" element={<AnalysisInsights />} />
          <Route path="/research" element={<ResearchWorkspace />} />
          <Route path="/collection" element={<CollectionDashboard />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </>
  )
}

export default App
