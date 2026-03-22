import { useState, useEffect, useCallback } from 'react';

const useHindiVoice = () => {
  const [transcript, setTranscript] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState(null);

  useEffect(() => {
    // Initialize Web Speech API for Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recog = new SpeechRecognition();
      recog.continuous = true; // Use continuous so it doesn't stop randomly
      recog.interimResults = true;
      recog.lang = 'hi-IN'; // Set language to Hindi

      recog.onresult = (event) => {
        const text = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setTranscript(text);
      };

      recog.onstart = () => {
        setIsListening(true);
      };

      recog.onend = () => {
        setIsListening(false);
      };

      recog.onerror = (event) => {
        console.error("Speech recognition error", event.error);
        setIsListening(false);
      };

      setRecognition(recog);
    } else {
      console.warn("Speech Recognition API not supported in this browser.");
    }
  }, []);

  const startListening = useCallback(() => {
    if (recognition) {
      setTranscript('');
      recognition.start();
    } else {
      alert("Speech Recognition API not supported in this browser.");
    }
  }, [recognition]);

  const stopListening = useCallback(() => {
    if (recognition) {
      recognition.stop();
    }
  }, [recognition]);

  const speakHindi = useCallback((text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      
      const setVoiceAndSpeak = () => {
        const voices = window.speechSynthesis.getVoices();
        // Find a Hindi voice
        const hindiVoice = voices.find(v => v.lang.includes('hi') || v.lang.includes('hi-IN'));
        
        if (hindiVoice) {
          utterance.voice = hindiVoice;
        } else {
          console.warn("No Hindi voice found. Falling back to default voice.");
        }
        
        // Ensure language is set properly for correct pronunciation even if voice is generic fallback
        utterance.lang = 'hi-IN';
        window.speechSynthesis.speak(utterance);
      };

      // Ensure voices are loaded (Chrome sometimes needs this)
      if (window.speechSynthesis.getVoices().length > 0) {
        setVoiceAndSpeak();
      } else {
        window.speechSynthesis.onvoiceschanged = () => {
          setVoiceAndSpeak();
          window.speechSynthesis.onvoiceschanged = null; // Clean up
        };
      }
    } else {
      console.warn("Text-to-speech not supported in this browser.");
    }
  }, []);

  return {
    transcript,
    isListening,
    startListening,
    stopListening,
    speakHindi
  };
};

export default useHindiVoice;
