import { motion } from 'framer-motion';
import { Sparkles, BrainCircuit, MessageSquare, Target, Zap } from 'lucide-react';

export default function Mentor() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)] relative">
      {/* Background decoration */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center z-10 max-w-2xl px-6"
      >
        <div className="mb-8 inline-flex items-center justify-center p-4 bg-primary/10 rounded-3xl border border-primary/20 shadow-[0_0_30px_rgba(var(--primary),0.1)]">
          <BrainCircuit className="w-12 h-12 text-primary animate-pulse" />
        </div>
        
        <h1 className="text-5xl font-headline font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-on-surface via-primary to-secondary">
          AI Mentor is Leveling Up
        </h1>
        
        <p className="text-on-surface-variant text-lg leading-relaxed mb-12">
          Your personal pedagogical guide is currently undergoing a deep synthetic upgrade. 
          Soon, it will analyze your entire study Vault to provide hyper-personalized 1-on-1 coaching.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
          <div className="bg-surface-container-low p-5 rounded-2xl border border-outline-variant/10 shadow-sm">
            <MessageSquare className="w-5 h-5 text-primary mb-3" />
            <h3 className="font-bold text-sm mb-1">Contextual Chat</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">Ask anything about your uploaded notes or past quizzes.</p>
          </div>
          <div className="bg-surface-container-low p-5 rounded-2xl border border-outline-variant/10 shadow-sm">
            <Target className="w-5 h-5 text-secondary mb-3" />
            <h3 className="font-bold text-sm mb-1">Weakness Analysis</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">AI detects your knowledge gaps and prepares custom curriculum.</p>
          </div>
          <div className="bg-surface-container-low p-5 rounded-2xl border border-outline-variant/10 shadow-sm">
            <Zap className="w-5 h-5 text-tertiary mb-3" />
            <h3 className="font-bold text-sm mb-1">Live Tutoring</h3>
            <p className="text-xs text-on-surface-variant leading-relaxed">Simulated voice sessions to help you through complex derivations.</p>
          </div>
        </div>

        <div className="mt-16 pt-8 border-t border-outline-variant/10 flex flex-col items-center">
          <div className="flex -space-x-3 mb-4">
             {[1,2,3,4].map(i => (
               <div key={i} className="w-10 h-10 rounded-full border-2 border-surface bg-surface-container-high overflow-hidden shadow-md">
                 <img src={`https://i.pravatar.cc/100?u=${i+10}`} alt="Early Access" />
               </div>
             ))}
             <div className="w-10 h-10 rounded-full border-2 border-surface bg-primary flex items-center justify-center text-[10px] font-bold text-on-primary shadow-md">
               +1.2k
             </div>
          </div>
          <p className="text-xs font-medium text-on-surface-variant">Joining 1,248 other aspirants in the early access queue.</p>
          
          <button className="mt-8 px-10 py-4 bg-on-surface hover:bg-on-surface-variant text-surface font-bold rounded-2xl transition-all shadow-[0_10px_30px_rgba(0,0,0,0.15)] flex items-center gap-3 group">
            <Sparkles className="w-5 h-5 group-hover:rotate-12 transition-transform" />
            Notify Me When Ready
          </button>
        </div>
      </motion.div>
    </div>
  );
}
