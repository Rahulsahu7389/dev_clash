import React, { useState, useEffect } from 'react';
import { Sparkles, Map, CheckCircle2, ArrowRight } from 'lucide-react';
import api from '../api/axios';
import { toast } from 'react-hot-toast';

export default function SyllabusRoadmap({ onTriggerOnboarding }) {
  const [syllabus, setSyllabus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchRoadmap = async () => {
    try {
      const res = await api.get('/syllabus/my-roadmap');
      if (res.data && res.data.data) {
        setSyllabus(res.data.data);
      } else {
        setSyllabus(null);
      }
    } catch (error) {
      console.error("Failed to fetch roadmap:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRoadmap();
  }, []);

  const handleComplete = async (topicName, isCompleted) => {
    if (isCompleted) return; // already completed

    // Optimistic UI Update
    const previousSyllabus = { ...syllabus };
    setSyllabus(prev => ({
      ...prev,
      chapters: prev.chapters.map(chapter => 
        chapter.topic_name === topicName 
          ? { ...chapter, is_completed: true, completed_at: new Date().toISOString() } 
          : chapter
      )
    }));

    try {
      await api.patch('/syllabus/complete-chapter', { topic_name: topicName });
      toast.success(`${topicName} mastered!`);
    } catch (error) {
      // Revert if failed
      setSyllabus(previousSyllabus);
      toast.error("Failed to update progress. Try again.");
    }
  };

  if (isLoading) {
    return (
      <div className="bg-surface-container-high rounded-xl p-6 flex flex-col items-center justify-center animate-pulse min-h-[300px]">
        <Map className="w-8 h-8 text-primary/50 mb-3" />
        <p className="text-on-surface-variant font-medium">Loading your AI roadmap...</p>
      </div>
    );
  }

  // Empty State
  if (!syllabus || !syllabus.chapters || syllabus.chapters.length === 0) {
    return (
      <div className="bg-surface-container-high rounded-xl p-8 flex flex-col items-center justify-center min-h-[300px] border border-dashed border-primary/30 h-full">
        <Sparkles className="w-12 h-12 text-primary mb-4" />
        <h3 className="font-headline text-xl font-bold mb-2">No Roadmap Found</h3>
        <p className="text-sm text-on-surface-variant text-center max-w-sm mb-6">
          Upload your syllabus PDF and let our AI construct your sequence.
        </p>
        <button 
          onClick={onTriggerOnboarding}
          className="bg-primary text-on-primary font-bold py-3 px-6 rounded-xl flex items-center gap-2 hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
        >
          Initialize AI Companion <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  // Render Syllabus Timeline
  return (
    <div className="bg-slate-900 p-6 rounded-xl border border-slate-700 shadow-xl flex flex-col max-h-[500px] h-full">
      <div className="flex justify-between items-center mb-6">
        <h3 className="font-headline text-lg font-bold flex items-center gap-2 text-white">
          <Map className="w-5 h-5 text-sky-400" /> 
          {syllabus.exam_track} Path
        </h3>
        <span className="text-xs font-bold bg-sky-900/50 text-sky-300 px-3 py-1 rounded-full border border-sky-500/30">
          {syllabus.chapters.filter(c => c.is_completed).length} / {syllabus.chapters.length}
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto pr-2 relative scrollbar-thin scrollbar-thumb-slate-700 hover:scrollbar-thumb-slate-600">
        <div className="space-y-0 relative z-0 ml-4 pb-4">
          {syllabus.chapters.map((chapter, index) => {
            const isLast = index === syllabus.chapters.length - 1;
            
            return (
               <div key={index} className="flex items-start group relative">
                  
                  {/* Vertical Line */}
                  {!isLast && (
                     <div className="absolute top-8 left-[11px] bottom-[-24px] w-[2px] bg-slate-700 -z-10 group-hover:bg-slate-600 transition-colors"></div>
                  )}

                  <button 
                    onClick={() => handleComplete(chapter.topic_name, chapter.is_completed)}
                    disabled={chapter.is_completed}
                    className="relative z-10 focus:outline-none transition-transform active:scale-95 bg-slate-900 pt-2 pb-6 pr-4"
                  >
                    {chapter.is_completed ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-500 bg-slate-900 rounded-full shrink-0" />
                    ) : (
                      <div className="w-6 h-6 rounded-full border-2 border-sky-500 bg-slate-900 flex items-center justify-center shrink-0 group-hover:border-sky-400 group-hover:shadow-[0_0_10px_rgba(56,189,248,0.5)] transition-all">
                      </div>
                    )}
                  </button>
                  
                  <div className={`flex-1 flex flex-col pt-1 pb-6 cursor-pointer transition-colors ${chapter.is_completed ? 'opacity-60' : 'hover:opacity-80'}`}
                       onClick={() => handleComplete(chapter.topic_name, chapter.is_completed)}>
                    <span className={`text-sm tracking-wide ${chapter.is_completed ? 'text-slate-400 line-through' : 'text-slate-100 font-semibold'}`}>
                      {chapter.topic_name}
                    </span>
                    {chapter.completed_at && (
                       <span className="text-[10px] text-slate-500 font-semibold mt-0.5">
                          {new Date(chapter.completed_at).toLocaleDateString()}
                       </span>
                    )}
                  </div>
               </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
