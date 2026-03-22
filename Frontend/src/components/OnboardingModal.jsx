import React, { useState } from 'react';
import api from '../api/axios';
import { Sparkles, Upload, Loader2, Calendar, Target } from 'lucide-react';
import { toast } from 'react-hot-toast'; // Assuming react-hot-toast is used, will fallback to alert if not or standard

export default function OnboardingModal({ onComplete }) {
  const [examTrack, setExamTrack] = useState('JEE');
  const [examDate, setExamDate] = useState('');
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      toast ? toast.error("Please upload your Master Syllabus PDF") : alert("Please upload your Master Syllabus PDF");
      return;
    }
    
    setIsLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('exam_track', examTrack);
      if (examDate) formData.append('exam_date', examDate);

      // Using the configured axios instance
      const res = await api.post('/syllabus/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (res.status === 200) {
        if (typeof toast !== 'undefined' && toast.success) {
            toast.success("Roadmap Generated!");
        } else {
            alert("Roadmap Generated!");
        }
        onComplete();
      }
    } catch (error) {
      console.error("Upload failed", error);
      if (typeof toast !== 'undefined' && toast.error) {
        toast.error("Failed to parse syllabus. Please try again.");
      } else {
        alert("Failed to parse syllabus. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg p-8 relative overflow-hidden shadow-2xl">
        {/* Glow effect */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-64 bg-primary/20 rounded-full blur-[80px] -z-10"></div>
        
        {/* Close Button */}
        <button 
          onClick={onComplete}
          className="absolute top-4 right-4 text-slate-500 hover:text-white transition-colors"
        >
          <span className="material-symbols-outlined">close</span>
        </button>
        
        <div className="flex items-center gap-3 justify-center mb-2">
          <Sparkles className="text-secondary w-6 h-6" />
          <h2 className="text-2xl font-bold text-white font-headline">Configure Your AI Companion</h2>
        </div>
        <p className="text-slate-400 text-center mb-8 text-sm">Upload your syllabus and set your targets. Our AI will build your personalized chronological roadmap.</p>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                <Target className="w-4 h-4 text-primary" /> Target Exam
              </label>
              <select 
                value={examTrack} 
                onChange={(e) => setExamTrack(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all appearance-none"
              >
                <option value="JEE">JEE (Joint Entrance Examination)</option>
                <option value="NEET">NEET (National Eligibility cum Entrance Test)</option>
                <option value="UPSC">UPSC (Civil Services Examination)</option>
                <option value="GATE">GATE (Graduate Aptitude Test in Engineering)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-primary" /> Targeting Exam Date
              </label>
              <input 
                type="date" 
                value={examDate}
                onChange={(e) => setExamDate(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all css-date-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                <Upload className="w-4 h-4 text-primary" /> Master Syllabus (PDF)
              </label>
              <div className="relative border-2 border-dashed border-slate-700 hover:border-primary/50 rounded-xl bg-slate-800/50 transition-colors cursor-pointer group">
                <input 
                  type="file" 
                  accept=".pdf"
                  onChange={(e) => setFile(e.target.files[0])}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="p-8 text-center pointer-events-none">
                  <Upload className="w-8 h-8 text-slate-500 mx-auto mb-3 group-hover:text-primary transition-colors" />
                  {file ? (
                    <div className="text-sm font-semibold text-primary">{file.name}</div>
                  ) : (
                    <>
                      <div className="text-sm font-medium text-slate-300">Click to upload or drag and drop</div>
                      <div className="text-xs text-slate-500 mt-1">PDF file strictly</div>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 text-white font-bold py-4 rounded-xl shadow-[0_0_20px_rgba(var(--primary),0.3)] transition-all flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed group relative overflow-hidden"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" /> 
                Parsing Syllabus with AI...
              </>
            ) : (
              <>
                Build My Roadmap
                <Sparkles className="w-4 h-4 group-hover:animate-pulse" />
              </>
            )}
            {/* Shimmer effect */}
            {!isLoading && <div className="absolute inset-0 -translate-x-full bg-white/20 skew-x-12 group-hover:animate-shimmer" />}
          </button>
        </form>
      </div>
    </div>
  );
}
