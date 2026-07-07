"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import Editor from "@monaco-editor/react";
import { questionApi, mockInterviewApi } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send, Play, CheckCircle2, XCircle, MessageSquare, BookOpen, Settings,
  Brain, ChevronDown, Loader2, Upload, Clock, Flag, ChevronRight, Mic, Square
} from "lucide-react";

const ALL_LANGS = [
  { id: "python", label: "Python 3", monacoId: "python" },
  { id: "cpp", label: "C++", monacoId: "cpp" },
  { id: "java", label: "Java", monacoId: "java" },
  { id: "javascript", label: "JavaScript", monacoId: "javascript" },
  { id: "sql", label: "SQL", monacoId: "sql" },
];

interface TestResult { input: string; expected_output: string; actual_output: string; passed: boolean; }

export default function InterviewRoom() {
  const { id } = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const mockId = searchParams.get("mock") ? Number(searchParams.get("mock")) : null;

  const [question, setQuestion] = useState<any>(null);
  const [mockData, setMockData] = useState<any>(null);
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");
  const [phase, setPhase] = useState<"coding" | "interview">("coding");
  const [runStatus, setRunStatus] = useState<"idle" | "running" | "submitting">("idle");
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [feedback, setFeedback] = useState("");
  const [allPassed, setAllPassed] = useState<boolean | null>(null);
  const [chat, setChat] = useState<{ role: string; content: string }[]>([]);
  const [message, setMessage] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [showLangDropdown, setShowLangDropdown] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [showEndConfirm, setShowEndConfirm] = useState(false);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [attempts, setAttempts] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isFinishing, setIsFinishing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const hasFinishedRef = useRef(false);

  // Load question
  useEffect(() => {
    if (!id) return;
    
    // Optimize: if we're in a mock interview, questions are already loaded in mockData
    if (mockId) {
      if (mockData?.questions) {
        const found = mockData.questions.find((q: any) => q.id === Number(id));
        if (found) {
          setQuestion(found);
          if (found.starter_code?.python) setCode(found.starter_code.python);
        }
      }
      return;
    }

    // Otherwise, fetch from the API (for standalone practice mode)
    questionApi.getQuestion(Number(id)).then((res) => {
      setQuestion(res.data);
      if (res.data.starter_code?.python) setCode(res.data.starter_code.python);
    }).catch(console.error);
  }, [id, mockId, mockData]);

  // Load mock interview data
  useEffect(() => {
    if (!mockId) return;
    mockInterviewApi.getDetail(mockId).then((res) => {
      setMockData(res.data);
      if (res.data.time_limit && res.data.created_at) {
        const startTime = new Date(res.data.created_at).getTime();
        const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
        const totalSeconds = res.data.time_limit * 60;
        setTimeLeft(Math.max(0, totalSeconds - elapsedSeconds));
      } else if (!timeLeft && res.data.time_limit) {
        setTimeLeft(res.data.time_limit * 60);
      }
    }).catch(console.error);
  }, [mockId]);

  // Timer countdown
  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0) return;
    
    // Pause the timer during the interview phase
    if (phase === "interview") return;

    timerRef.current = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev !== null && prev <= 1) { clearInterval(timerRef.current!); return 0; }
        return prev ? prev - 1 : null;
      });
    }, 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [timeLeft !== null, phase]);

  // Time up effect
  useEffect(() => {
    if (timeLeft === 0 && mockId && !hasFinishedRef.current) {
      hasFinishedRef.current = true;
      finishInterview();
      alert("Time is up! Your test has been submitted automatically.");
    }
  }, [timeLeft, mockId]);

  useEffect(() => { if (!question?.starter_code) return; const s = question.starter_code[language]; if (s) setCode(s); }, [language, question]);
  
  // Sync language if the current one is not available for this question
  useEffect(() => {
    const isSql = mockData?.topic?.toLowerCase().includes('sql') || question?.topic?.toLowerCase().includes('sql') || question?.title?.toLowerCase().includes('sql');
    const avail = isSql ? ALL_LANGS.filter(l => l.id === 'sql') : (question?.starter_code && Object.keys(question.starter_code).length > 0
      ? ALL_LANGS.filter(l => Object.keys(question.starter_code).includes(l.id))
      : ALL_LANGS);
    if (avail.length > 0 && !avail.find(l => l.id === language)) {
      setLanguage(avail[0].id);
    }
  }, [question, language, mockData]);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chat]);

  const formatTime = (s: number) => { const m = Math.floor(s / 60); return `${m}:${String(s % 60).padStart(2, "0")}`; };

  const savePerf = useCallback(async (status: string) => {
    if (!mockId || !id) return;
    const timeSpent = Math.floor((Date.now() - questionStartTime) / 1000);
    await mockInterviewApi.savePerformance(mockId, Number(id), {
      status, time_spent: timeSpent, code, language, attempts,
      interview_brief: chat.length > 0 ? chat.map(m => `${m.role}: ${m.content}`).join('\n').slice(0, 500) : '',
    }).catch(console.error);
  }, [mockId, id, questionStartTime, code, language, attempts, chat]);

  const handleRun = async () => {
    setRunStatus("running"); setTestResults([]); setErrorMessage(null); setAllPassed(null); setShowResults(true);
    try {
      const res = await questionApi.runCode({ question_id: Number(id), code, language });
      setTestResults(res.data.test_results); setErrorMessage(res.data.error_message);
      setFeedback(res.data.feedback); setAllPassed(res.data.all_passed);
    } catch (err: any) { setErrorMessage(err.response?.data?.error || "Failed to run code"); }
    finally { setRunStatus("idle"); }
  };

  const handleSubmit = async () => {
    setRunStatus("submitting"); setTestResults([]); setErrorMessage(null); setAllPassed(null); setShowResults(true);
    setAttempts(a => a + 1);
    try {
      const res = await questionApi.submitCode({ question_id: Number(id), code, language });
      setTestResults(res.data.test_results); setErrorMessage(res.data.error_message);
      setFeedback(res.data.feedback); setAllPassed(res.data.all_passed);
      if (res.data.all_passed && res.data.interview_session_id) {
        setSessionId(res.data.interview_session_id);
        setChat([{ role: "assistant", content: res.data.initial_question }]);
        setPhase("interview");
        await savePerf("accepted");
      }
    } catch (err: any) { setErrorMessage(err.response?.data?.error || "Submission failed"); }
    finally { setRunStatus("idle"); }
  };

  const sendMessage = async () => {
    if (!message.trim() || !sessionId || chatLoading) return;
    const userMsg = message.trim(); setMessage("");
    setChat(prev => [...prev, { role: "user", content: userMsg }]);
    setChatLoading(true);
    try { const res = await questionApi.interviewChat(sessionId, userMsg); setChat(res.data.chat_history); }
    catch (err) { console.error(err); } finally { setChatLoading(false); }
  };

  const recognitionRef = useRef<any>(null);

  const startRecording = async () => {
    try {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert("Speech recognition is not supported in this browser. Please use Chrome.");
        return;
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.lang = "en-US";
      recognitionRef.current = recognition;

      recognition.onresult = (event: any) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            transcript += event.results[i][0].transcript;
          }
        }
        if (transcript) {
          setMessage(prev => prev ? prev + " " + transcript : transcript);
        }
      };

      recognition.onerror = (event: any) => {
        console.error("Speech recognition error:", event.error);
        if (event.error === "not-allowed") {
          alert("Microphone access denied. Please allow microphone access.");
        }
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognition.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Mic error:", err);
      alert("Microphone access denied or not available.");
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }
  };

  const goToQuestion = async (qId: number, idx: number) => {
    if (mockId) {
      await savePerf(phase === "interview" ? "accepted" : "pending");
      await mockInterviewApi.update(mockId, { current_question_index: idx });
    }
    setPhase("coding"); setChat([]); setSessionId(null); setTestResults([]); setAllPassed(null);
    setShowResults(false); setErrorMessage(null); setFeedback(""); setAttempts(0);
    setQuestionStartTime(Date.now());
    router.push(`/interview/${qId}?mock=${mockId}`);
  };

  const finishInterview = async () => {
    if (!mockId) {
      router.push('/');
      return;
    }
    setIsFinishing(true);
    try {
      await savePerf(phase === "interview" ? "accepted" : "skipped");
      const totalTime = mockData ? (mockData.time_limit * 60) - (timeLeft || 0) : 0;
      await mockInterviewApi.finish(mockId, { total_time_spent: totalTime });
      router.push(`/results/${mockId}`);
    } catch (err) {
      console.error("Failed to finish interview:", err);
      setIsFinishing(false);
      alert("Something went wrong while finishing the test. Please try again.");
    }
  };

  if (!question) return (
    <div className="flex h-screen items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-indigo-400" /><span className="ml-3 text-slate-400">Loading...</span>
    </div>
  );

  const isSql = mockData?.topic?.toLowerCase().includes('sql') || question?.topic?.toLowerCase().includes('sql') || question?.title?.toLowerCase().includes('sql');
  const availableLangs = isSql ? ALL_LANGS.filter(l => l.id === 'sql') : (question?.starter_code && Object.keys(question.starter_code).length > 0
    ? ALL_LANGS.filter(l => Object.keys(question.starter_code).includes(l.id))
    : ALL_LANGS);
  const curLang = availableLangs.find(l => l.id === language) || availableLangs[0] || ALL_LANGS[0];
  const questions = mockData?.questions || [];
  const curIdx = questions.findIndex((q: any) => q.id === Number(id));
  const performances = mockData?.performances || [];

  return (
    <div className="flex h-screen overflow-hidden bg-[#0a0a0f]">
      {/* ══ QUESTION SIDEBAR (only in mock mode) ══ */}
      {mockId && questions.length > 0 && (
        <div className="w-14 md:w-16 h-full border-r border-white/5 flex flex-col items-center py-3 gap-2 shrink-0 bg-[#080810]">
          <div className="text-[8px] font-bold text-slate-600 uppercase mb-1">Questions</div>
          {questions.map((q: any, i: number) => {
            const perf = performances.find((p: any) => p.question?.id === q.id);
            const isCurrent = q.id === Number(id);
            const solved = perf?.status === "accepted";
            return (
              <button key={q.id} onClick={() => goToQuestion(q.id, i)}
                className={`w-9 h-9 md:w-10 md:h-10 rounded-xl text-xs font-bold flex items-center justify-center transition-all border-2 ${
                  isCurrent ? "border-indigo-500 bg-indigo-500/20 text-indigo-400"
                  : solved ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                  : "border-white/5 text-slate-600 hover:border-white/15 hover:text-slate-400"
                }`}>
                {solved ? <CheckCircle2 className="w-4 h-4" /> : i + 1}
              </button>
            );
          })}
        </div>
      )}

      {/* ══ LEFT PANEL — Problem ══ */}
      <div className={`h-full border-r border-white/5 overflow-y-auto shrink-0 ${phase === "interview" ? "w-[22%]" : mockId ? "w-[28%]" : "w-[30%]"}`}>
        <div className="sticky top-0 z-10 bg-[#0a0a0f]/90 backdrop-blur-sm border-b border-white/5 px-4 py-3">
          <div className="flex items-center gap-2 text-indigo-400 mb-1">
            <BookOpen className="w-4 h-4" />
            <span className="font-semibold uppercase tracking-widest text-[10px]">Problem</span>
            {mockId && <span className="ml-auto text-[10px] text-slate-600 font-bold">Q{curIdx + 1}/{questions.length}</span>}
          </div>
          <h2 className="text-lg font-bold">{question.title}</h2>
          <div className="flex gap-2 mt-2">
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
              question.difficulty === "Easy" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : question.difficulty === "Medium" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
              : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
            }`}>{question.difficulty}</span>
          </div>
        </div>
        <div className="px-4 py-4 space-y-4">
          <div className="text-slate-300 text-sm leading-relaxed leetcode-description" dangerouslySetInnerHTML={{ __html: question.description }} />
          {question.examples?.map((ex: any, i: number) => (
            <div key={i} className="bg-white/3 rounded-xl border border-white/5 p-3 break-words">
              <h4 className="text-xs font-bold text-slate-400 uppercase mb-2">Example {i + 1}</h4>
              <div className="space-y-2 text-sm font-mono">
                <div>
                  <span className="text-slate-500">Input: </span>
                  <div className="text-sky-300 mt-1 whitespace-pre-wrap bg-black/20 p-2 rounded-lg border border-white/5 text-xs">{ex.input}</div>
                </div>
                <div>
                  <span className="text-slate-500">Output: </span>
                  <div className="text-emerald-300 mt-1 whitespace-pre-wrap bg-black/20 p-2 rounded-lg border border-white/5 text-xs">{ex.output}</div>
                </div>
                {ex.explanation && <div className="pt-2 mt-2 border-t border-white/5 text-xs text-slate-400 font-sans leading-relaxed">{ex.explanation}</div>}
              </div>
            </div>
          ))}
          {question.constraints && (
            <div className="bg-white/3 rounded-xl border border-white/5 p-3">
              <h4 className="text-xs font-bold text-slate-400 uppercase mb-1">Constraints</h4>
              {question.constraints.split("\n").map((c: string, i: number) => <p key={i} className="text-xs font-mono text-slate-400">• {c}</p>)}
            </div>
          )}
        </div>
      </div>

      {/* ══ CENTER — Editor + Results ══ */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        {/* Toolbar with Timer */}
        <div className="h-12 flex items-center justify-between px-3 border-b border-white/5 bg-white/2 shrink-0">
          <div className="flex items-center gap-3">
            {/* Language */}
            <div className="relative">
              <button onClick={() => setShowLangDropdown(!showLangDropdown)}
                className="flex items-center gap-2 text-xs font-bold text-slate-300 bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-lg border border-white/10">
                <Settings className="w-3 h-3 text-slate-500" />{curLang.label}<ChevronDown className="w-3 h-3 text-slate-500" />
              </button>
              {showLangDropdown && (
                <div className="absolute top-full left-0 mt-1 bg-[#1a1a2e] border border-white/10 rounded-lg overflow-hidden shadow-xl z-50">
                  {availableLangs.map(l => (
                    <button key={l.id} onClick={() => { setLanguage(l.id); setShowLangDropdown(false); }}
                      className={`block w-full text-left px-4 py-2 text-xs font-medium ${language === l.id ? "bg-indigo-600/20 text-indigo-400" : "text-slate-300 hover:bg-white/5"}`}>{l.label}</button>
                  ))}
                </div>
              )}
            </div>
            {/* Timer */}
            {timeLeft !== null && (
              <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold border ${
                timeLeft < 300 ? "bg-rose-500/10 text-rose-400 border-rose-500/20 animate-pulse"
                : timeLeft < 600 ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                : "bg-white/5 text-slate-300 border-white/10"
              }`}>
                <Clock className="w-3 h-3" />{formatTime(timeLeft)}
              </div>
            )}
          </div>
          {/* Actions */}
          <div className="flex gap-2">
            {mockId && (
              <button onClick={() => setShowEndConfirm(true)}
                className="flex items-center gap-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-bold px-3 py-1.5 rounded-lg border border-rose-500/20 transition-colors mr-2">
                <Flag className="w-3 h-3" /> End Test
              </button>
            )}
            <button onClick={handleRun} disabled={runStatus !== "idle"}
              className="flex items-center gap-1.5 bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-bold px-3 py-1.5 rounded-lg border border-white/10 disabled:opacity-50">
              {runStatus === "running" ? <><Loader2 className="w-3 h-3 animate-spin" />Running...</> : <><Play className="w-3 h-3 fill-current" />Run</>}
            </button>
            <button onClick={handleSubmit} disabled={runStatus !== "idle"}
              className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-3 py-1.5 rounded-lg disabled:opacity-50">
              {runStatus === "submitting" ? <><Loader2 className="w-3 h-3 animate-spin" />Submitting...</> : <><Upload className="w-3 h-3" />Submit</>}
            </button>
          </div>
        </div>

        {/* Editor */}
        <div className={showResults ? "h-[55%]" : "flex-1"}>
          <Editor height="100%" language={curLang.monacoId} theme="vs-dark" value={code}
            onChange={(v) => setCode(v || "")}
            options={{ fontSize: 14, minimap: { enabled: false }, padding: { top: 16 }, scrollBeyondLastLine: false,
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace", lineNumbers: "on", cursorBlinking: "smooth" }} />
        </div>

        {/* Results */}
        {showResults ? (
          <div className="flex-1 border-t border-white/5 bg-[#0d0d14] overflow-y-auto">
            <div className="sticky top-0 z-10 bg-[#0d0d14] flex items-center justify-between px-4 py-2 border-b border-white/5">
              <span className="text-xs font-bold text-slate-400 uppercase">Test Results</span>
              <button onClick={() => setShowResults(false)} className="text-[10px] text-slate-500 hover:text-slate-300 px-2 py-0.5 rounded hover:bg-white/5">✕</button>
            </div>
            <div className="p-3 space-y-2">
              {runStatus !== "idle" && testResults.length === 0 && (
                <div className="flex items-center justify-center py-6 text-slate-500 text-sm"><Loader2 className="w-4 h-4 mr-2 animate-spin" />Processing...</div>
              )}
              {allPassed !== null && (
                <div className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold ${allPassed ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                  {allPassed ? <><CheckCircle2 className="w-4 h-4" />All Passed! 🎉</> : <><XCircle className="w-4 h-4" />Failed</>}
                </div>
              )}
              {errorMessage && <div className="bg-rose-500/5 border border-rose-500/20 rounded-xl p-3 text-rose-300 text-xs font-mono">{errorMessage}</div>}
              {feedback && !allPassed && <div className="bg-amber-500/5 border border-amber-500/15 rounded-xl p-3 text-amber-300 text-xs">💡 {feedback}</div>}
              {testResults.map((tr, i) => (
                <div key={i} className={`rounded-xl border p-3 ${tr.passed ? "bg-emerald-500/5 border-emerald-500/15" : "bg-rose-500/5 border-rose-500/15"}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {tr.passed ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <XCircle className="w-3.5 h-3.5 text-rose-400" />}
                    <span className={`font-bold text-xs ${tr.passed ? "text-emerald-400" : "text-rose-400"}`}>Test {i + 1}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 font-mono text-[10px]">
                    <div><span className="text-slate-500 block mb-0.5">Input</span><div className="bg-black/20 rounded p-1.5 text-slate-300">{tr.input}</div></div>
                    <div><span className="text-slate-500 block mb-0.5">Expected</span><div className="bg-black/20 rounded p-1.5 text-emerald-300">{tr.expected_output}</div></div>
                    <div><span className="text-slate-500 block mb-0.5">Output</span><div className={`bg-black/20 rounded p-1.5 ${tr.passed ? "text-emerald-300" : "text-rose-300"}`}>{tr.actual_output}</div></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="h-10 border-t border-white/5 bg-[#0d0d14] flex items-center justify-center shrink-0">
            <span className="text-slate-600 text-xs">Run or Submit to see results</span>
          </div>
        )}
      </div>

      {/* ══ RIGHT — AI Interviewer ══ */}
      <AnimatePresence>
        {phase === "interview" && (
          <motion.div initial={{ width: 0, opacity: 0 }} animate={{ width: "28%", opacity: 1 }}
            exit={{ width: 0, opacity: 0 }} transition={{ duration: 0.4 }}
            className="h-full border-l border-white/5 flex flex-col bg-[#0a0a0f] overflow-hidden">
            <div className="h-12 flex items-center gap-2 px-4 border-b border-white/5 shrink-0">
              <MessageSquare className="w-4 h-4 text-purple-400" />
              <span className="text-sm font-bold">Alex</span>
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[10px] font-bold border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />Live
              </span>
              <div className="ml-auto flex gap-2">
                {/* Next Question */}
                {mockId && curIdx < questions.length - 1 && (
                  <button onClick={() => goToQuestion(questions[curIdx + 1].id, curIdx + 1)}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 text-[10px] font-bold border border-indigo-500/20 hover:bg-indigo-500/20">
                    Next Q<ChevronRight className="w-3 h-3" />
                  </button>
                )}
                {/* Finish Interview */}
                {mockId && (
                  <button onClick={() => setShowEndConfirm(true)}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-400 text-[10px] font-bold border border-rose-500/20 hover:bg-rose-500/20">
                    <Flag className="w-3 h-3" />Finish
                  </button>
                )}
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {chat.map((msg, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[90%] p-3 rounded-2xl text-sm leading-relaxed ${
                    msg.role === "user" ? "bg-indigo-600/20 text-indigo-100 border border-indigo-500/20 rounded-br-md"
                    : "bg-white/5 text-slate-300 border border-white/10 rounded-bl-md"
                  }`}>
                    {msg.role === "assistant" && <div className="flex items-center gap-1 mb-1 text-[10px] text-purple-400 font-bold uppercase"><Brain className="w-3 h-3" />Alex</div>}
                    {msg.content}
                  </div>
                </motion.div>
              ))}
              {chatLoading && (
                <div className="flex justify-start"><div className="bg-white/5 border border-white/10 rounded-2xl p-3 text-sm text-slate-500 flex items-center gap-2"><Loader2 className="w-3 h-3 animate-spin" />Thinking...</div></div>
              )}
              <div ref={chatEndRef} />
            </div>
            
            {/* Suggested Quick Replies */}
            {chat.length > 0 && chat[chat.length - 1].role === "assistant" && !chatLoading && (
              <div className="flex gap-2 px-4 py-2 border-t border-white/5 bg-[#0a0a0f] overflow-x-auto no-scrollbar shrink-0">
                <button onClick={() => { 
                    setMessage("I'm not exactly sure, can you give me a small hint?"); 
                    setTimeout(() => document.getElementById("chat-send-btn")?.click(), 50);
                  }}
                  className="whitespace-nowrap px-3 py-1.5 rounded-full border border-white/10 bg-white/5 text-slate-300 text-[10px] font-medium hover:bg-white/10 transition-colors">
                  💡 Need a hint
                </button>
                <button onClick={() => { 
                    setMessage("I'd like to skip this and move on to the next question."); 
                    setTimeout(() => document.getElementById("chat-send-btn")?.click(), 50);
                  }}
                  className="whitespace-nowrap px-3 py-1.5 rounded-full border border-white/10 bg-white/5 text-slate-300 text-[10px] font-medium hover:bg-white/10 transition-colors">
                  ⏭️ Next question
                </button>
                {mockId ? (
                  <button onClick={() => setShowEndConfirm(true)}
                    className="whitespace-nowrap px-3 py-1.5 rounded-full border border-rose-500/20 bg-rose-500/10 text-rose-400 text-[10px] font-medium hover:bg-rose-500/20 transition-colors">
                    🛑 End Test
                  </button>
                ) : (
                  <button onClick={() => router.push('/')}
                    className="whitespace-nowrap px-3 py-1.5 rounded-full border border-rose-500/20 bg-rose-500/10 text-rose-400 text-[10px] font-medium hover:bg-rose-500/20 transition-colors">
                    🛑 Exit to Dashboard
                  </button>
                )}
              </div>
            )}

            <div className="p-3 border-t border-white/5 shrink-0">
              <div className="relative flex items-center gap-2">
                <div className="relative flex-1">
                  <input value={message} onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                    placeholder={isTranscribing ? "Transcribing audio..." : "Type your answer..."} disabled={chatLoading || isTranscribing}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:border-indigo-500 outline-none pr-12 disabled:opacity-50" />
                  <button id="chat-send-btn" onClick={sendMessage} disabled={chatLoading || !message.trim() || isTranscribing}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 hover:bg-indigo-600 rounded-lg disabled:opacity-30">
                    <Send className="w-4 h-4" />
                  </button>
                </div>
                <button 
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={chatLoading || isTranscribing}
                  className={`p-3 rounded-xl border flex items-center justify-center transition-all disabled:opacity-50 ${
                    isRecording 
                      ? "bg-rose-500/20 border-rose-500 text-rose-400 animate-pulse" 
                      : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10"
                  }`}
                  title={isRecording ? "Stop Recording" : "Record Answer"}
                >
                  {isTranscribing ? <Loader2 className="w-4 h-4 animate-spin" /> : isRecording ? <Square className="w-4 h-4 fill-current" /> : <Mic className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ══ END TEST CONFIRMATION MODAL ══ */}
      <AnimatePresence>
        {showEndConfirm && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#0a0a0f] border border-white/10 p-6 rounded-2xl max-w-sm w-full shadow-2xl relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-rose-500 to-orange-500" />
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-rose-500/10 flex items-center justify-center shrink-0">
                  <Flag className="w-5 h-5 text-rose-400" />
                </div>
                <h3 className="text-lg font-bold text-white">End Test?</h3>
              </div>
              <p className="text-slate-400 text-sm mb-6 leading-relaxed">
                Are you sure you want to end this test? All your submitted progress will be saved, but you won't be able to return to answer more questions.
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowEndConfirm(false)}
                  disabled={isFinishing}
                  className="px-4 py-2 rounded-xl text-sm font-bold text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={finishInterview}
                  disabled={isFinishing}
                  className="px-4 py-2 rounded-xl text-sm font-bold bg-rose-600 hover:bg-rose-500 text-white shadow-[0_0_15px_rgba(225,29,72,0.3)] hover:shadow-[0_0_20px_rgba(225,29,72,0.5)] transition-all flex items-center gap-2 disabled:opacity-50 disabled:hover:bg-rose-600"
                >
                  {isFinishing ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Finishing...</>
                  ) : (
                    "Yes, End Test"
                  )}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
