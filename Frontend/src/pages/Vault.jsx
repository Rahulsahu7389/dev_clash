export default function Vault() {
  return (
    <div className="h-[calc(100vh-4rem)] flex overflow-hidden w-full -mt-8 -mx-8 relative">
      {/* Left Pane: Context & Document Management */}
      <section className="w-[420px] h-full bg-surface-container-low flex flex-col border-r border-outline-variant/5">
        <div className="p-6">
          <h2 className="font-headline text-xl font-bold mb-1">Study Vault</h2>
          <p className="text-xs text-on-surface-variant font-medium uppercase tracking-widest mb-6">Contextual Documents</p>

          {/* Drag & Drop Zone */}
          <div className="border-2 border-dashed border-primary/20 rounded-xl p-8 text-center bg-surface-container-lowest hover:border-primary/40 transition-all cursor-pointer group">
            <span className="material-symbols-outlined text-4xl text-primary/40 group-hover:scale-110 transition-transform mb-3">upload_file</span>
            <p className="text-sm font-semibold">Drop PDF notes here</p>
            <p className="text-[10px] text-on-surface-variant mt-1">Supports OCR & Equation Parsing</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-4">
          <h3 className="text-[10px] font-bold text-outline uppercase tracking-widest">Active Sources (4)</h3>

          {/* Document List Items */}
          <div className="bg-surface-container-high p-4 rounded-xl flex items-center gap-4 group cursor-pointer hover:bg-surface-container-highest transition-colors">
            <div className="w-10 h-10 rounded-lg bg-error/10 flex items-center justify-center text-error">
              <span className="material-symbols-outlined">picture_as_pdf</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate">Advanced_Calculus_Lec3.pdf</p>
              <p className="text-[10px] text-on-surface-variant">12 Pages • Annotated</p>
            </div>
            <span className="material-symbols-outlined text-outline opacity-0 group-hover:opacity-100 transition-opacity">more_vert</span>
          </div>

          <div className="bg-surface-container-high p-4 rounded-xl flex items-center gap-4 group cursor-pointer hover:bg-surface-container-highest transition-colors">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
              <span className="material-symbols-outlined">description</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate">Quantum_Mechanics_Summary</p>
              <p className="text-[10px] text-on-surface-variant">Shared by Mentor • 3 mins ago</p>
            </div>
            <span className="material-symbols-outlined text-outline opacity-0 group-hover:opacity-100 transition-opacity">more_vert</span>
          </div>

          <div className="bg-surface-container-high p-4 rounded-xl flex items-center gap-4 group cursor-pointer hover:bg-surface-container-highest transition-colors">
            <div className="w-10 h-10 rounded-lg bg-tertiary/10 flex items-center justify-center text-tertiary">
              <span className="material-symbols-outlined">video_library</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate">Electrostatics_Video_Transcript</p>
              <p className="text-[10px] text-on-surface-variant">Auto-generated • Dec 12</p>
            </div>
            <span className="material-symbols-outlined text-outline opacity-0 group-hover:opacity-100 transition-opacity">more_vert</span>
          </div>

          {/* Recessed "Empty State" Logic Hint */}
          <div className="bg-surface-container-lowest p-4 rounded-xl border border-outline-variant/10 text-center py-8">
            <span className="material-symbols-outlined text-outline/30 text-3xl mb-2">add_circle</span>
            <p className="text-[11px] text-on-surface-variant">Link more context to improve AI precision</p>
          </div>
        </div>
      </section>

      {/* Right Pane: The Sophisticated Chat UI */}
      <section className="flex-1 flex flex-col bg-surface relative overflow-hidden">
        {/* Chat Header */}
        <div className="h-16 px-8 border-b border-outline-variant/5 flex items-center justify-between glass-[45,52,73,0.6] backdrop-blur-md z-10 w-full bg-surface-container-low/80">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-secondary animate-pulse"></div>
            <h2 className="font-headline font-semibold text-sm">Doubt Solver AI <span className="text-secondary font-normal text-[10px] ml-2 px-1.5 py-0.5 rounded border border-secondary/30 bg-secondary/10">v4.2 PRO</span></h2>
          </div>
          <div className="flex gap-2">
            <button className="p-2 rounded-lg hover:bg-surface-container-high text-outline transition-colors"><span className="material-symbols-outlined text-lg">history</span></button>
            <button className="p-2 rounded-lg hover:bg-surface-container-high text-outline transition-colors"><span className="material-symbols-outlined text-lg">settings</span></button>
          </div>
        </div>

        {/* Chat Message Thread */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8 pb-32">
          {/* User Message */}
          <div className="flex justify-end items-start gap-4">
            <div className="max-w-[70%] bg-surface-container-high p-4 rounded-2xl rounded-tr-none text-sm leading-relaxed">
              Can you explain the derivation of the Schrödinger equation from these notes? I'm specifically struggling with the Hamiltonian operator section on page 4.
            </div>
            <div className="w-8 h-8 rounded-full bg-primary/20 flex-shrink-0 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-sm">person</span>
            </div>
          </div>

          {/* AI Response Bubble */}
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 rounded-full bg-secondary/20 flex-shrink-0 flex items-center justify-center">
              <span className="material-symbols-outlined text-secondary text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
            </div>
            <div className="max-w-[85%] space-y-4">
              <div className="bg-surface-container-high/60 backdrop-blur-md border-l-2 border-secondary p-5 rounded-2xl rounded-tl-none text-sm leading-relaxed text-on-surface">
                <p className="mb-4">Based on your Lec3 PDF, the Schrödinger equation derivation focuses on the conservation of energy principle. Here is the mathematical breakdown for the Hamiltonian Operator (Ĥ):</p>
                
                {/* Math/Markdown Component */}
                <div className="bg-surface-container-lowest p-4 rounded-lg font-mono text-secondary mb-4 border border-secondary/10">
                  ĤΨ = EΨ <br />
                  Where Ĥ = -ħ²/2m ∇² + V(r,t)
                </div>
                
                <p className="mb-6">The operator represents the sum of kinetic and potential energy. I've found a relevant video snippet that visualizes the operator's effect on wave functions:</p>
                
                {/* Video Embed Component */}
                <div className="aspect-video rounded-xl overflow-hidden bg-black border border-outline-variant/20 shadow-lg mb-4">
                  <iframe allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen className="w-full h-full" frameBorder="0" src="https://www.youtube.com/embed/dQw4w9WgXcQ?controls=0" title="Concept Explanation"></iframe>
                </div>
                
                <div className="flex items-center gap-2 mt-4">
                  <button className="flex items-center gap-1.5 text-[10px] font-bold text-secondary uppercase tracking-widest px-3 py-1.5 rounded-full border border-secondary/20 hover:bg-secondary/10 transition-colors">
                    <span className="material-symbols-outlined text-xs">bookmark</span> Save to Notebook
                  </button>
                  <button className="flex items-center gap-1.5 text-[10px] font-bold text-tertiary uppercase tracking-widest px-3 py-1.5 rounded-full border border-tertiary/20 hover:bg-tertiary/10 transition-colors">
                    <span className="material-symbols-outlined text-xs">thumb_up</span> Correct
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Input Area: The Command Center */}
        <div className="absolute bottom-0 left-0 right-0 p-8 pt-0">
          <div className="max-w-4xl mx-auto bg-surface-container-high/80 backdrop-blur-md p-2 rounded-2xl border border-outline-variant/10 shadow-2xl">
            <div className="relative flex items-end gap-2 bg-surface-container-lowest rounded-xl p-2">
              <button className="p-2.5 rounded-lg text-outline hover:text-primary hover:bg-primary/5 transition-all">
                <span className="material-symbols-outlined">attach_file</span>
              </button>
              <button className="p-2.5 rounded-lg text-outline hover:text-primary hover:bg-primary/5 transition-all">
                <span className="material-symbols-outlined">mic</span>
              </button>
              <textarea className="flex-1 bg-transparent border-none outline-none focus:ring-0 text-sm py-2.5 px-2 resize-none placeholder:text-outline/40" placeholder="Ask from notes..." rows="1"></textarea>
              <button className="bg-primary hover:bg-primary-container text-on-primary p-2.5 rounded-lg flex items-center justify-center transition-all shadow-lg shadow-primary/20">
                <span className="material-symbols-outlined">send</span>
              </button>
            </div>
            <div className="flex items-center gap-4 px-3 py-2">
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                <span className="text-[10px] text-secondary font-bold uppercase tracking-wider">Deep Analysis Mode</span>
              </div>
              <div className="h-3 w-[1px] bg-outline-variant/20"></div>
              <span className="text-[10px] text-on-surface-variant">Press <kbd className="px-1 py-0.5 rounded bg-surface-container-high border border-outline-variant/20">Cmd + K</kbd> for shortcuts</span>
            </div>
          </div>
        </div>
      </section>

      {/* Floating AI Bubble */}
      <div className="fixed bottom-6 right-6 z-50">
        <button className="w-14 h-14 bg-gradient-to-br from-primary to-primary-container rounded-full flex items-center justify-center text-on-primary shadow-xl shadow-primary/30 hover:scale-110 active:scale-95 transition-all group">
          <span className="material-symbols-outlined text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
          <div className="absolute right-16 px-4 py-2 bg-surface-container-highest rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity text-xs font-bold border border-primary/20 pointer-events-none">
            Quick Summary
          </div>
        </button>
      </div>
    </div>
  );
}
