"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { mockInterviewApi } from "@/lib/api";
import { motion } from "framer-motion";
import {
  Code2, Database, Server, Loader2, Clock, Zap,
  ChevronRight, Sparkles, ArrowLeft
} from "lucide-react";
import Link from "next/link";

const TOPICS = [
  { id: "dsa", label: "DSA", desc: "Data Structures & Algorithms", icon: Code2, color: "indigo" },
  { id: "sql", label: "SQL", desc: "Database Queries", icon: Database, color: "emerald" },
  { id: "system_design", label: "System Design", desc: "Architecture & Scalability", icon: Server, color: "purple" },
];

const SUBTOPICS: Record<string, string[]> = {
  dsa: ["Arrays", "Strings", "Trees", "Graphs", "Dynamic Programming", "Linked Lists", "Stacks & Queues", "Sorting", "Searching", "Recursion", "Hashing", "Greedy"],
  sql: ["Joins", "Subqueries", "Window Functions", "Aggregations", "Indexes", "CTEs", "Normalization"],
  system_design: ["Caching", "Load Balancing", "Databases", "Microservices", "Message Queues", "CDN", "API Design"],
};

const DIFFICULTIES = [
  { id: "Easy", color: "emerald" },
  { id: "Medium", color: "amber" },
  { id: "Hard", color: "rose" },
];

const QUESTION_COUNTS = [1, 3, 5];
const TIME_LIMITS = [
  { value: 15, label: "15 min" },
  { value: 30, label: "30 min" },
  { value: 45, label: "45 min" },
  { value: 60, label: "60 min" },
];

export default function StartInterview() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [selectedSubtopics, setSelectedSubtopics] = useState<string[]>([]);
  const [difficulty, setDifficulty] = useState("Medium");
  const [numQuestions, setNumQuestions] = useState(3);
  const [timeLimit, setTimeLimit] = useState(30);
  const [generating, setGenerating] = useState(false);

  const toggleSubtopic = (st: string) => {
    setSelectedSubtopics((prev) =>
      prev.includes(st) ? prev.filter((s) => s !== st) : [...prev, st]
    );
  };

  const handleStart = async () => {
    if (!topic) return;
    setGenerating(true);
    try {
      const res = await mockInterviewApi.generate({
        topic, subtopics: selectedSubtopics, difficulty,
        num_questions: numQuestions, time_limit: timeLimit,
      });
      const mockId = res.data.id;
      const firstQuestionId = res.data.questions[0]?.id;
      if (firstQuestionId) {
        router.push(`/interview/${firstQuestionId}?mock=${mockId}`);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to generate interview. Please try again.");
    } finally {
      setGenerating(false);
    }
  };

  const colorMap: Record<string, string> = {
    indigo: "border-indigo-500/30 bg-indigo-500/10 text-indigo-400",
    emerald: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
    purple: "border-purple-500/30 bg-purple-500/10 text-purple-400",
    amber: "border-amber-500/30 bg-amber-500/10 text-amber-400",
    rose: "border-rose-500/30 bg-rose-500/10 text-rose-400",
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4 md:p-8">
      <div className="w-full max-w-3xl">
        {/* Back Link */}
        <Link href="/" className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-300 text-sm mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-bold uppercase tracking-widest mb-4">
            <Sparkles className="w-3 h-3" /> Custom Interview
          </div>
          <h1 className="text-3xl md:text-4xl font-bold mb-3">Configure Your Mock Interview</h1>
          <p className="text-slate-500 text-sm">Select your preferences and we'll generate a tailored interview</p>
        </motion.div>

        <div className="space-y-8">
          {/* ── Step 1: Topic ── */}
          <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">1. Choose Topic</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {TOPICS.map((t) => (
                <button key={t.id} onClick={() => { setTopic(t.id); setSelectedSubtopics([]); }}
                  className={`p-5 rounded-2xl border-2 text-left transition-all ${
                    topic === t.id
                      ? `${colorMap[t.color]} border-2`
                      : "border-white/5 bg-white/2 hover:border-white/10"
                  }`}>
                  <t.icon className={`w-6 h-6 mb-3 ${topic === t.id ? "" : "text-slate-600"}`} />
                  <div className="font-bold text-sm">{t.label}</div>
                  <div className={`text-xs mt-1 ${topic === t.id ? "opacity-80" : "text-slate-600"}`}>{t.desc}</div>
                </button>
              ))}
            </div>
          </motion.section>

          {/* ── Step 2: Subtopics (optional) ── */}
          {topic && (
            <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">2. Focus Areas <span className="text-slate-600">(optional)</span></h3>
              <p className="text-[10px] text-slate-600 mb-4">Leave empty for a mix of all subtopics</p>
              <div className="flex flex-wrap gap-2">
                {SUBTOPICS[topic]?.map((st) => (
                  <button key={st} onClick={() => toggleSubtopic(st)}
                    className={`px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                      selectedSubtopics.includes(st)
                        ? "bg-indigo-500/15 border-indigo-500/30 text-indigo-400"
                        : "border-white/10 text-slate-500 hover:border-white/20 hover:text-slate-300"
                    }`}>
                    {st}
                  </button>
                ))}
              </div>
            </motion.section>
          )}

          {/* ── Step 3: Difficulty ── */}
          {topic && (
            <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">3. Difficulty Level</h3>
              <div className="flex gap-3">
                {DIFFICULTIES.map((d) => (
                  <button key={d.id} onClick={() => setDifficulty(d.id)}
                    className={`flex-1 py-3 rounded-xl border-2 text-sm font-bold transition-all ${
                      difficulty === d.id
                        ? colorMap[d.color]
                        : "border-white/5 text-slate-500 hover:border-white/10"
                    }`}>
                    {d.id}
                  </button>
                ))}
              </div>
            </motion.section>
          )}

          {/* ── Step 4: Questions & Time ── */}
          {topic && (
            <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Number of Questions */}
                <div>
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <Zap className="w-3 h-3" /> 4. Questions
                  </h3>
                  <div className="flex gap-3">
                    {QUESTION_COUNTS.map((n) => (
                      <button key={n} onClick={() => setNumQuestions(n)}
                        className={`flex-1 py-3 rounded-xl border-2 text-sm font-bold transition-all ${
                          numQuestions === n
                            ? "border-indigo-500/30 bg-indigo-500/10 text-indigo-400"
                            : "border-white/5 text-slate-500 hover:border-white/10"
                        }`}>
                        {n}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Time Limit */}
                <div>
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <Clock className="w-3 h-3" /> 5. Time Limit
                  </h3>
                  <div className="flex gap-2">
                    {TIME_LIMITS.map((t) => (
                      <button key={t.value} onClick={() => setTimeLimit(t.value)}
                        className={`flex-1 py-3 rounded-xl border-2 text-xs font-bold transition-all ${
                          timeLimit === t.value
                            ? "border-indigo-500/30 bg-indigo-500/10 text-indigo-400"
                            : "border-white/5 text-slate-500 hover:border-white/10"
                        }`}>
                        {t.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </motion.section>
          )}

          {/* ── Start Button ── */}
          {topic && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="pt-4">
              <button onClick={handleStart} disabled={generating}
                className="w-full py-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm flex items-center justify-center gap-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                {generating ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Generating your interview...</>
                ) : (
                  <><Sparkles className="w-5 h-5" /> Start Interview <ChevronRight className="w-4 h-4" /></>
                )}
              </button>
              {generating && (
                <p className="text-center text-slate-600 text-xs mt-3">This may take 15-20 seconds as we craft your questions...</p>
              )}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
