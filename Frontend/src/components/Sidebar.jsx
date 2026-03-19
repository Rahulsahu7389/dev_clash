import { Link, useLocation } from 'react-router-dom';

export default function Sidebar() {
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', icon: 'dashboard', path: '/' },
    { name: 'Vault', icon: 'inventory_2', path: '/vault' },
    { name: 'Quiz', icon: 'quiz', path: '/quiz' },
    { name: 'Arena', icon: 'sports_esports', path: '/arena' },
    { name: 'Mentor', icon: 'psychology', path: '/mentor' },
  ];

  return (
    <aside className="h-screen w-64 fixed left-0 top-0 z-40 bg-[#131b2e] border-r border-cyan-500/10 shadow-[4px_0_24px_rgba(6,182,212,0.05)] flex flex-col py-6">
      <div className="px-6 mb-10">
        <h1 className="text-2xl font-bold text-cyan-500 tracking-tighter font-headline">PrepSarthi</h1>
        <p className="text-[10px] tracking-widest uppercase text-slate-500 font-label mt-1">Elite Tier</p>
      </div>

      <nav className="flex-1 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 transition-all duration-300 ease-in-out hover:translate-x-1 ${
                isActive 
                  ? 'bg-cyan-500/10 text-cyan-400 border-r-2 border-cyan-500 font-bold' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span className="material-symbols-outlined">{item.icon}</span>
              <span className="font-headline text-lg">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="px-4 mt-auto">
        <button className="w-full py-3 px-4 bg-gradient-to-r from-primary to-primary-container text-on-primary font-bold rounded-xl shadow-lg shadow-primary/20 hover:scale-[1.02] transition-transform">
          Upgrade to Pro
        </button>
        <div className="mt-6 flex items-center gap-3 px-2">
          <img alt="User Profile Avatar" className="w-10 h-10 rounded-full bg-surface-container-high" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAdJ3dOcKznXez6bRdiVao2KA8G_wyIdA8zj3Wymmk4t1kU5XXNfftoSGTitTXavljB036NZXUTX8j9YIeMzsHaLsFh_CNDXtYSpWdFDzgeXud9Kvqt-dALN9t6SgDACdAskX2ErDStGDVFQHv7iAx5oiMwK_abWpPq5_Mj8-5ugmz7qKbNeO5LqOJII5CqPTGWZgv3T7KMyGV1cBoID3ntc_qNeGsmp2qROCvrVIMCN8bfjNhTtNmom-I_eadtJPhfwtRbJTW4J4c" />
          <div className="overflow-hidden">
            <p className="text-sm font-bold truncate">Alex Chen</p>
            <p className="text-[10px] text-slate-500 uppercase tracking-tighter">Rank #422</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
