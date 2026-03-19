import { Link } from 'react-router-dom';

export default function Dashboard() {
  return (
    <>
      {/* Top Banner / Hero */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2 bg-surface-container-low p-8 rounded-xl relative overflow-hidden flex flex-col justify-between">
          <div className="relative z-10">
            <h2 className="font-headline text-4xl font-bold tracking-tight mb-2">Welcome back, Alex.</h2>
            <p className="text-on-surface-variant flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-tertiary"></span>
              Your focus score is 12% higher than yesterday.
            </p>
          </div>
          <div className="mt-8 flex gap-8 items-end relative z-10">
            <div>
              <p className="text-[10px] font-label tracking-widest text-on-surface-variant uppercase mb-1">Current Rank</p>
              <div className="flex items-center gap-3">
                <div className="p-3 bg-primary/10 rounded-xl border border-primary/20 shadow-[0_0_15px_rgba(76,215,246,0.2)]">
                  <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>workspace_premium</span>
                </div>
                <div>
                  <p className="font-headline text-2xl font-bold">Scholar</p>
                  <p className="text-xs text-primary">Top 4% Overall</p>
                </div>
              </div>
            </div>
            <div className="h-12 w-[1px] bg-outline-variant/30 mb-1"></div>
            <div>
              <p className="text-[10px] font-label tracking-widest text-on-surface-variant uppercase mb-1">Total Experience</p>
              <p className="font-headline text-3xl font-bold">14,280 <span className="text-sm text-on-surface-variant font-body">XP</span></p>
            </div>
          </div>
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-[100px] -mr-32 -mt-32"></div>
        </div>

        {/* Hero Widget (The Hook) */}
        <div className="bg-surface-container-high rounded-xl p-1 flex flex-col">
          <div className="flex-1 bg-surface-container-lowest rounded-lg p-6 flex flex-col items-center justify-center text-center border border-primary/20 shadow-[inset_0_0_20px_rgba(var(--primary),0.05)]">
            <div className="mb-4 p-4 rounded-full bg-primary/10">
              <span className="material-symbols-outlined text-primary scale-150" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
            </div>
            <Link to="/quiz" className="font-headline text-xl font-bold text-on-primary bg-gradient-to-br from-primary to-primary-container px-8 py-4 rounded-xl shadow-[0_0_30px_rgba(var(--primary),0.3)] hover:scale-105 transition-transform mb-4 inline-block">
              Start Daily Revision
            </Link>
            <p className="text-sm text-on-surface-variant max-w-[200px]">
              <span className="text-error font-bold">5 topics</span> are about to fade from your memory.
            </p>
          </div>
        </div>
      </div>

      {/* Bento Grid Main */}
      <div className="grid grid-cols-12 gap-6">
        {/* Consistency Grid */}
        <div className="col-span-12 lg:col-span-8 bg-surface-container-low p-6 rounded-xl">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-headline text-lg font-bold">Consistency Pulse</h3>
            <div className="flex items-center gap-2 text-[10px] font-label tracking-widest text-on-surface-variant uppercase">
              <span>Less</span>
              <div className="flex gap-1">
                <div className="heatmap-cell bg-surface-container-high"></div>
                <div className="heatmap-cell bg-tertiary/20"></div>
                <div className="heatmap-cell bg-tertiary/40"></div>
                <div className="heatmap-cell bg-tertiary/70"></div>
                <div className="heatmap-cell bg-tertiary"></div>
              </div>
              <span>More</span>
            </div>
          </div>
          
          {/* Simple Heatmap Mockup */}
          <div className="flex gap-1 overflow-x-auto pb-2">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="grid grid-rows-7 gap-1 flex-shrink-0">
                <div className="heatmap-cell bg-tertiary/60"></div>
                <div className="heatmap-cell bg-tertiary/20"></div>
                <div className="heatmap-cell bg-tertiary/80"></div>
                <div className="heatmap-cell bg-surface-container-high"></div>
                <div className="heatmap-cell bg-tertiary/40"></div>
                <div className="heatmap-cell bg-tertiary/90"></div>
                <div className="heatmap-cell bg-tertiary"></div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-outline-variant/10 flex justify-between">
            <div className="text-sm text-on-surface-variant">
              Max Streak: <span className="text-tertiary font-bold">14 Days</span>
            </div>
            <div className="text-sm text-on-surface-variant">
              Last 30 Days: <span className="text-on-surface font-bold">4,120 XP</span>
            </div>
          </div>
        </div>

        {/* Targeted Mastery */}
        <div className="col-span-12 lg:col-span-4 bg-surface-container-high p-6 rounded-xl flex flex-col">
          <h3 className="font-headline text-lg font-bold mb-6">Targeted Mastery</h3>
          <div className="relative flex-1 flex items-center justify-center">
            {/* SVG Radar Chart Mockup */}
            <svg className="w-full max-w-[200px] h-auto drop-shadow-[0_0_10px_rgba(221,183,255,0.1)]" viewBox="0 0 100 100">
              <circle className="text-outline-variant/20" cx="50" cy="50" fill="none" r="45" stroke="currentColor" strokeWidth="0.5"></circle>
              <circle className="text-outline-variant/20" cx="50" cy="50" fill="none" r="30" stroke="currentColor" strokeWidth="0.5"></circle>
              <circle className="text-outline-variant/20" cx="50" cy="50" fill="none" r="15" stroke="currentColor" strokeWidth="0.5"></circle>
              <path d="M50 15 L80 40 L70 75 L30 75 L20 40 Z" fill="rgba(221,183,255,0.2)" stroke="#ddb7ff" strokeWidth="1"></path>
              <line className="text-outline-variant/20" stroke="currentColor" strokeWidth="0.5" x1="50" x2="50" y1="50" y2="5"></line>
              <line className="text-outline-variant/20" stroke="currentColor" strokeWidth="0.5" x1="50" x2="95" y1="50" y2="40"></line>
              <line className="text-outline-variant/20" stroke="currentColor" strokeWidth="0.5" x1="50" x2="75" y1="50" y2="90"></line>
              <line className="text-outline-variant/20" stroke="currentColor" strokeWidth="0.5" x1="50" x2="25" y1="50" y2="90"></line>
              <line className="text-outline-variant/20" stroke="currentColor" strokeWidth="0.5" x1="50" x2="5" y1="50" y2="40"></line>
            </svg>
            <div className="absolute bottom-0 left-0 right-0 glass-card p-3 rounded-lg border-l-2 border-secondary">
              <p className="text-[10px] font-label text-secondary mb-1">AI INSIGHT</p>
              <p className="text-xs text-on-surface leading-tight">Your <b>Quantitative Aptitude</b> has dropped by 8% this week. Suggest a 15min focus session.</p>
            </div>
          </div>
        </div>

        {/* Activity Feed */}
        <div className="col-span-12 lg:col-span-8 bg-surface-container-high rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-outline-variant/10 flex justify-between items-center">
            <h3 className="font-headline text-lg font-bold">Activity Feed</h3>
            <button className="text-xs text-primary font-bold hover:underline">View All</button>
          </div>
          <div className="p-6 space-y-6">
            <div className="flex gap-4 group">
              <div className="w-10 h-10 rounded-lg bg-surface-container-lowest flex items-center justify-center text-primary border border-outline-variant/20 group-hover:border-primary/50 transition-colors">
                <span className="material-symbols-outlined">verified</span>
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <p className="text-sm font-bold">Mock Exam Completed</p>
                  <span className="text-[10px] text-on-surface-variant font-label">2H AGO</span>
                </div>
                <p className="text-xs text-on-surface-variant mt-1">Advanced Physics - Section 4. Score: 92/100</p>
              </div>
            </div>
            {/* Add more activity items as needed */}
          </div>
        </div>

        {/* Urgent Review */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          <div className="bg-surface-container-low p-6 rounded-xl">
            <h3 className="font-headline text-lg font-bold mb-4">Urgent Review</h3>
            <div className="space-y-4">
              <div className="p-4 bg-surface-container-lowest rounded-lg border-l-2 border-error/50">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-bold">Organic Chemistry</span>
                  <span className="text-error text-[10px] font-bold">Low Retent.</span>
                </div>
                <div className="w-full bg-surface-container-high h-1 rounded-full overflow-hidden">
                  <div className="bg-error h-full" style={{ width: '22%' }}></div>
                </div>
              </div>
            </div>
            <button className="w-full mt-4 py-2 text-xs font-bold text-on-surface-variant border border-outline-variant/20 rounded-lg hover:bg-surface-container-high transition-colors">
              Analyze Weaknesses
            </button>
          </div>
        </div>
      </div>
{/* Global Notification Mockup */}
<div className="fixed bottom-6 right-6 z-50 glass-card p-4 rounded-xl border border-primary/20 shadow-2xl flex items-center gap-4 max-w-sm">
        <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center text-primary flex-shrink-0">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
        </div>
        <div>
          <p className="text-sm font-bold text-on-surface">Study Session Invite</p>
          <p className="text-xs text-on-surface-variant">Saurav is studying <b>Fluid Mechanics</b>. Join the arena?</p>
          <div className="flex gap-2 mt-2">
            <button className="px-3 py-1 bg-primary text-on-primary text-[10px] font-bold rounded-md">Join Now</button>
            <button className="px-3 py-1 bg-surface-container-highest text-on-surface-variant text-[10px] font-bold rounded-md">Later</button>
          </div>
        </div>
      </div>
    </>
  );
}
