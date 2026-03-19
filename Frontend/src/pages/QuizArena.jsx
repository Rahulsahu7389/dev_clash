import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit, Loader2, Sparkles, Send, Target, ChevronRight, CheckCircle, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';

export default function QuizArena() {
  const [topic, setTopic] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [score, setScore] = useState(0);
  
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [isCorrect, setIsCorrect] = useState(null);
  
  const [approachText, setApproachText] = useState('');
  const [isCheckingApproach, setIsCheckingApproach] = useState(false);
  const [aiTutorFeedback, setAiTutorFeedback] = useState('');
  
  const [isFinished, setIsFinished] = useState(false);
  const navigate = useNavigate();

  const handleStartRevision = async () => {
    if (!topic.trim()) return;
    setIsGenerating(true);
    try {
      const response = await api.post('/quiz/generate', { topic });
      setQuestions(response.data);
      setCurrentIndex(0);
      setScore(0);
      setIsFinished(false);
      resetTurnState();
    } catch (err) {
      console.error(err);
      alert('Failed to generate quiz. Make sure the backend is responding.');
    } finally {
      setIsGenerating(false);
    }
  };

  const resetTurnState = () => {
    setSelectedAnswer(null);
    setIsCorrect(null);
    setApproachText('');
    setAiTutorFeedback('');
    setIsCheckingApproach(false);
  };

  const handleAnswerSelect = (option) => {
    if (selectedAnswer !== null) return;
    
    setSelectedAnswer(option);
    const correct = option === questions[currentIndex].correct_answer;
    setIsCorrect(correct);
    
    if (correct) {
      setScore(prev => prev + 1);
    }
  };

  const handleDiagnose = async () => {
    if (!approachText.trim()) return;
    setIsCheckingApproach(true);
    try {
      const q = questions[currentIndex];
      const res = await api.post('/doubt/approach', {
        question: q.question,
        correct_answer: q.correct_answer,
        user_logic: approachText
      });
      // Handle the text response
      const feedback = res.data.feedback || res.data.message || res.data;
      setAiTutorFeedback(typeof feedback === 'string' ? feedback : "Review this concept to master it.");
    } catch (err) {
      console.error(err);
      setAiTutorFeedback("The AI Tutor is currently offline. Please review your logic again.");
    } finally {
      setIsCheckingApproach(false);
    }
  };

  const handleNext = async () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(prev => prev + 1);
      resetTurnState();
    } else {
      setIsFinished(true);
      try {
        await api.post('/quiz/submit', { topic, quality: score });
      } catch (err) {
        console.error("Failed to submit score", err);
      }
    }
  };

  // ================= SCENE: SETUP =================
  if (questions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-6rem)] p-8 relative">
        <div className="absolute inset-0 bg-primary/5 blur-[120px] rounded-full pointer-events-none -z-10 w-2/3 h-2/3 m-auto" />
        
        {isGenerating ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }} 
            animate={{ opacity: 1, scale: 1 }} 
            className="w-full max-w-md bg-surface-container-high border border-primary/30 p-8 rounded-2xl shadow-[0_0_30px_rgba(var(--primary),0.15)] flex flex-col items-center gap-6"
          >
            <motion.div 
              animate={{ rotate: 360, boxShadow: ["0px 0px 0px rgba(14,165,233,0)", "0px 0px 20px rgba(14,165,233,0.5)", "0px 0px 0px rgba(14,165,233,0)"] }}
              transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
              className="p-4 rounded-full bg-primary/10"
            >
              <BrainCircuit className="w-10 h-10 text-primary" />
            </motion.div>
            <div className="text-center space-y-2">
              <h2 className="text-xl font-headline font-bold text-on-surface animate-pulse">Synthesizing Arena...</h2>
              <p className="text-sm text-on-surface-variant">Generating dynamic challenges for <span className="font-bold text-primary">{topic}</span></p>
            </div>
            <div className="w-full h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-primary"
                initial={{ width: "0%" }}
                animate={{ width: "100%" }}
                transition={{ duration: 4, repeat: Infinity }}
              />
            </div>
          </motion.div>
        ) : (
          <motion.div 
            initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }} 
            className="w-full max-w-lg bg-surface-container-low border border-outline-variant/20 p-8 rounded-2xl shadow-xl space-y-6"
          >
            <div className="flex flex-col gap-2 items-center text-center">
              <div className="p-3 bg-secondary/10 rounded-xl mb-2 text-secondary">
                <Target className="w-8 h-8" />
              </div>
              <h1 className="text-3xl font-headline font-bold text-on-surface">Daily Revision Arena</h1>
              <p className="text-sm text-on-surface-variant">Target specific concepts to beat the forgetting curve and maximize your ELO.</p>
            </div>
            
            <div className="space-y-4">
              <div className="relative group">
                <input 
                  type="text" 
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Enter a topic (e.g. Thermodynamics, Graph Theory)" 
                  className="w-full bg-surface-container-lowest border border-outline-variant/30 text-on-surface px-4 py-4 rounded-xl focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all placeholder:text-outline/50 outline-none"
                  onKeyDown={(e) => e.key === 'Enter' && handleStartRevision()}
                />
              </div>
              
              <button 
                onClick={handleStartRevision}
                disabled={!topic.trim()}
                className="w-full py-4 bg-gradient-to-r from-primary to-primary-container text-on-primary font-bold rounded-xl shadow-lg shadow-primary/20 hover:shadow-primary/40 hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:hover:translate-y-0 flex items-center justify-center gap-2"
              >
                <Sparkles className="w-5 h-5" />
                Initialize Arena
              </button>
            </div>
          </motion.div>
        )}
      </div>
    );
  }

  // ================= SCENE: VICTORY =================
  if (isFinished) {
    return (
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center min-h-[calc(100vh-6rem)] p-8 relative"
      >
        <div className="absolute inset-0 bg-emerald-500/5 blur-[120px] rounded-full pointer-events-none -z-10 w-2/3 h-2/3 m-auto" />
        
        <div className="w-full max-w-md bg-surface-container-high border border-outline-variant/20 p-8 rounded-2xl shadow-xl flex flex-col items-center text-center gap-6">
          <div className="w-24 h-24 bg-emerald-500/10 text-emerald-500 rounded-full flex items-center justify-center border-4 border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.3)]">
            <span className="text-4xl font-headline font-bold">{score}/{questions.length}</span>
          </div>
          
          <div>
            <h2 className="text-2xl font-headline font-bold text-on-surface mb-2">Arena Conquered</h2>
            <p className="text-sm text-on-surface-variant">Your SRS interval has been officially calibrated for <span className="font-bold text-primary">{topic}</span>.</p>
          </div>
          
          <button 
            onClick={() => navigate('/')}
            className="w-full py-3 bg-surface-container-lowest border border-outline-variant/30 hover:bg-surface-container-highest text-on-surface font-bold rounded-xl transition-all"
          >
            Return to Dashboard
          </button>
        </div>
      </motion.div>
    );
  }

  // ================= SCENE: ACTIVE QUIZ =================
  const currentQuestion = questions[currentIndex];

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 h-full relative">
      {/* Quiz Header */}
      <div className="flex justify-between items-center mb-10 bg-surface-container-high py-3 px-6 rounded-2xl border border-outline-variant/10 shadow-lg">
        <div className="flex items-center gap-3">
          <span className="p-2 bg-primary/10 text-primary rounded-lg shadow-inner"><Target className="w-5 h-5" /></span>
          <div>
            <p className="text-[10px] text-on-surface-variant font-label tracking-widest uppercase mb-0.5">Active Target</p>
            <p className="font-bold text-sm text-on-surface">{topic}</p>
          </div>
        </div>
        <div className="flex gap-2">
          {questions.map((_, i) => (
            <div 
              key={i} 
              className={`w-10 h-2 rounded-full transition-all duration-300 ${i === currentIndex ? 'bg-primary shadow-[0_0_10px_rgba(14,165,233,0.5)]' : i < currentIndex ? 'bg-primary/40' : 'bg-surface-container-highest'}`}
            />
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={currentIndex}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="space-y-8"
        >
          {/* Question Display */}
          <div className="mb-8">
            <span className="text-primary font-bold tracking-wider text-xs uppercase mb-3 block">Question {currentIndex + 1} of {questions.length}</span>
            <h2 className="text-2xl font-headline text-on-surface font-medium leading-relaxed">{currentQuestion.question}</h2>
          </div>

          {/* Options Grid */}
          <div className="grid grid-cols-1 gap-4">
            {currentQuestion.options.map((option, idx) => {
              const isSelected = selectedAnswer === option;
              const isActualCorrect = option === currentQuestion.correct_answer;
              
              // Styling logic post-selection
              let optStyle = "bg-surface-container-low hover:bg-surface-container-high border-outline-variant/20 text-on-surface-variant hover:text-on-surface";
              let animationProps = {};
              
              if (selectedAnswer !== null) {
                if (isSelected && isCorrect) {
                  optStyle = "bg-emerald-500/10 border-emerald-500 ring-2 ring-emerald-500/50 text-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.2)]";
                  animationProps = { scale: [1, 1.02, 1] };
                } else if (isSelected && !isCorrect) {
                  optStyle = "bg-rose-500/10 border-rose-500 ring-2 ring-rose-500/50 text-rose-500";
                  animationProps = { x: [0, -10, 10, -10, 10, 0], transition: { duration: 0.4 } };
                } else if (isActualCorrect) {
                  optStyle = "bg-emerald-500/5 border-emerald-500/50 text-emerald-500/70";
                } else {
                  optStyle = "bg-surface-container-lowest border-outline-variant/10 opacity-50";
                }
              }

              return (
                <motion.button
                  key={idx}
                  onClick={() => handleAnswerSelect(option)}
                  animate={animationProps}
                  className={`relative w-full text-left p-5 rounded-2xl border transition-all duration-300 font-medium ${optStyle}`}
                  disabled={selectedAnswer !== null}
                >
                  <div className="flex justify-between items-center pr-8">
                    <span>{option}</span>
                    {selectedAnswer !== null && isActualCorrect && (
                      <CheckCircle className="absolute right-5 w-5 h-5 text-emerald-500" />
                    )}
                    {selectedAnswer !== null && isSelected && !isCorrect && (
                      <XCircle className="absolute right-5 w-5 h-5 text-rose-500" />
                    )}
                  </div>
                </motion.button>
              );
            })}
          </div>

          {/* Post Answer UI */}
          {selectedAnswer !== null && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="pt-6"
            >
              {/* Correct Explanation */}
              {isCorrect && (
                <div className="bg-emerald-500/10 border border-emerald-500/20 p-5 rounded-xl">
                  <p className="text-emerald-500 font-bold mb-2 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" /> Bullseye!
                  </p>
                  <p className="text-on-surface-variant text-sm">{currentQuestion.explanation}</p>
                </div>
              )}

              {/* Incorrect Diagnostics Panel */}
              {!isCorrect && (
                <div className="bg-surface-container-high border-t-8 border-rose-500/80 p-6 rounded-2xl shadow-xl mt-4">
                  <h3 className="text-rose-500 font-headline font-bold mb-2 flex items-center gap-2 text-lg">
                    <BrainCircuit className="w-5 h-5" /> Logic Break Detected
                  </h3>
                  <p className="text-sm text-on-surface-variant mb-6">Explain your approach to the AI Tutor to identify where the misconception happened.</p>
                  
                  {!aiTutorFeedback ? (
                    <div className="space-y-4">
                      <textarea 
                        value={approachText}
                        onChange={(e) => setApproachText(e.target.value)}
                        placeholder="Where did your logic break down? I initially thought X because..."
                        className="w-full bg-surface-container-lowest border border-outline-variant/20 rounded-xl p-4 text-sm focus:border-secondary focus:ring-1 focus:ring-secondary/50 outline-none text-on-surface resize-none h-32"
                        disabled={isCheckingApproach}
                      />
                      <button 
                        onClick={handleDiagnose}
                        disabled={!approachText.trim() || isCheckingApproach}
                        className="w-full flex justify-center items-center gap-2 py-3 bg-secondary/10 hover:bg-secondary/20 text-secondary border border-secondary/30 font-bold rounded-xl transition-all disabled:opacity-50"
                      >
                        {isCheckingApproach ? (
                          <><Loader2 className="w-4 h-4 animate-spin" /> Deep Analyzing...</>
                        ) : (
                          <><Sparkles className="w-4 h-4" /> Diagnose Approach</>
                        )}
                      </button>
                    </div>
                  ) : (
                    <motion.div 
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="bg-secondary/10 border border-secondary/30 p-5 rounded-xl"
                    >
                      <p className="text-xs text-secondary font-bold tracking-widest uppercase mb-3 flex items-center gap-2">
                        <Sparkles className="w-4 h-4" /> AI Tutor Insight
                      </p>
                      <p className="text-on-surface text-sm leading-relaxed">{aiTutorFeedback}</p>
                    </motion.div>
                  )}
                </div>
              )}

              {/* Next Button Footer */}
              <div className="mt-8 flex justify-end">
                <button 
                  onClick={handleNext}
                  className="px-8 py-3 bg-on-surface hover:bg-on-surface-variant text-surface font-bold rounded-xl flex items-center gap-2 transition-colors shadow-xl"
                >
                  {currentIndex === questions.length - 1 ? 'Finish Arena' : 'Next Question'}
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
