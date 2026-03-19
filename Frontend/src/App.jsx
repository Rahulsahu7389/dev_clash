import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import DashboardLayout from './layouts/DashboardLayout';
import Dashboard from './pages/Dashboard';
import Vault from './pages/Vault';

// Placeholder Pages
const Quiz = () => <div className="text-2xl font-headline">Quiz Arena</div>;
const Arena = () => <div className="text-2xl font-headline">Live Arena</div>;
const Mentor = () => <div className="text-2xl font-headline">AI Mentor</div>;

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
