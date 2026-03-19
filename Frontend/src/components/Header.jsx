export default function Header() {
  return (
    <header className="fixed top-0 right-0 left-64 h-16 z-30 bg-[#0b1326]/80 backdrop-blur-xl flex justify-between items-center px-8">
      <div className="flex items-center gap-4 bg-surface-container-lowest px-4 py-1.5 rounded-full border border-outline-variant/20 w-96">
        <span className="material-symbols-outlined text-outline text-sm">search</span>
        <input className="bg-transparent border-none focus:ring-0 text-sm w-full placeholder:text-outline/50 outline-none" placeholder="Search topics, modules..." type="text" />
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-4">
          <button className="relative text-slate-400 hover:text-cyan-400 transition-all scale-95 active:scale-90">
            <span className="material-symbols-outlined">military_tech</span>
          </button>
          <button className="relative text-slate-400 hover:text-cyan-400 transition-all scale-95 active:scale-90">
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
            </span>
          </button>
          <button className="relative text-slate-400 hover:text-cyan-400 transition-all scale-95 active:scale-90">
            <span className="material-symbols-outlined">show_chart</span>
          </button>
        </div>

        <div className="h-8 w-[1px] bg-outline-variant/20"></div>

        <button className="flex items-center gap-2 text-slate-400 font-medium font-label text-[10px] tracking-widest uppercase hover:text-cyan-200 transition-all">
          Profile
          <img alt="User Avatar" className="w-8 h-8 rounded-lg bg-surface-container-high" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBq5vJkUsIxgvl0KfqNOpArkxpSUTRJWSUdGKsv_yEQcbKzK-MOtaGRxm4EZxbIUReM1A-d7Hgmo44VcCFubLjM-Z7f0Mi-waf8Rse0NWwuzesvyVc-5xCjF7DpM0crT7YgLp8WPIyqBq2a9PALCzPXJEPAhOACnP8RFwLMwMvIZEZxmERiL2fCsbkN_BDgzI4X4Z2mP3TSNy0FK7_AYHV0O6-p1AWjL1jJl6q4ibl3w7tM0ONdH1Npb5Y-5vk6mMtpgckCgjTIqyo" />
        </button>
      </div>
    </header>
  );
}
