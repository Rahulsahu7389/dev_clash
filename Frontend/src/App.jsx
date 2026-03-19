import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import Dashboard from './pages/Dashboard';
import Vault from './pages/Vault';
import Mentor from './pages/Mentor';

// Placeholder Pages
const Quiz = () => <div className="text-2xl font-headline text-white">Quiz Arena (Ongoing Simulation)</div>;
const Arena = () => <div className="text-2xl font-headline text-white">Live Battle Arena</div>;

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="vault" element={<Vault />} />
          <Route path="quiz" element={<Quiz />} />
          <Route path="arena" element={<Arena />} />
          <Route path="mentor" element={<Mentor />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
