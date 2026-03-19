import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import Dashboard from './pages/Dashboard';
import Vault from './pages/Vault';
import Auth from './pages/Auth';

// Placeholder Pages
const Quiz = () => <div className="text-2xl font-headline">Quiz Arena</div>;
const Arena = () => <div className="text-2xl font-headline">Live Arena</div>;
const Mentor = () => <div className="text-2xl font-headline">AI Mentor</div>;

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('access_token');
  if (!token) {
    return <Navigate to="/auth" replace />;
  }
  return children;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/auth" element={<Auth />} />

        <Route path="/" element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="vault" element={<Vault />} />
          <Route path="quiz" element={<Quiz />} />
          <Route path="arena" element={<Arena />} />
          <Route path="mentor" element={<Mentor />} />
        </Route>
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
