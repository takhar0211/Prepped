"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { mockInterviewApi } from "@/lib/api";
import { motion } from "framer-motion";
import { CheckCircle2, XCircle, Clock, Brain, ArrowLeft, Trophy, Target, Zap, SkipForward, Code2, MessageSquare, ListTodo, TrendingUp } from "lucide-react";
import Link from "next/link";

export default function ResultsPage() {
  const { mockId } = useParams();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (!mockId) return;
    mockInterviewApi.getDetail(Number(mockId)).then(res => setData(res.data)).catch(console.error);
  }, [mockId]);

  if (!data) return (
    <div className="flex h-screen items-center justify-center">
      <div className="w-8 h-8 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
      <span className="ml-3 text-slate-400">Loading your AI performance report...</span>
    </div>
  );

  const perfs = data.performances || [];
  const solved = perfs.filter((p: any) => p.status === "accepted").length;
  const total = perfs.length;
  const totalTime = data.total_time_spent || 0;
  
  // Parse the LLM report
  let report = null;
  if (data.performance_summary) {
    try {
      report = JSON.parse(data.performance_summary);
    } catch (e) {
      console.error("Failed to parse report", e);
    }
  }

  // Fallback scores if report is missing
  const overallScore = report?.overall_score || (total > 0 ? Math.round((solved / total) * 100) : 0);
  const codingScore = report?.coding_score || overallScore;
  const interviewScore = report?.interview_score || overallScore;

  const formatTime = (s: number) => {
    if (s < 60) return `${s}s`;
    const m = Math.floor(s / 60); const sec = s % 60;
    return `${m}m ${sec}s`;
  };

  const statusIcon = (s: string) => {
    if (s === "accepted") return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
    if (s === "wrong_answer") return <XCircle className="w-5 h-5 text-rose-400" />;
    return <SkipForward className="w-5 h-5 text-slate-500" />;
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <Link href="/" className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-300 text-sm mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>

        {/* ── Header ── */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border-2 border-indigo-500/30 flex items-center justify-center mx-auto mb-4">
            <Trophy className="w-12 h-12 text-indigo-400" />
          </div>
          <h1 className="text-4xl font-bold mb-3">Performance Report</h1>
          <p className="text-slate-400 text-sm capitalize flex items-center justify-center gap-3">
            <span>{data.topic.replace("_", " ")}</span> • 
            <span>{data.difficulty}</span> • 
            <span>{total} Questions</span> •
            <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{formatTime(totalTime)}</span>
          </p>
          {report?.summary && (
            <div className="mt-6 max-w-2xl mx-auto p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/20">
              <p className="text-sm text-indigo-200 leading-relaxed font-medium">"{report.summary}"</p>
              <div className="mt-2 text-[10px] font-bold text-indigo-400 uppercase tracking-widest flex items-center justify-center gap-1">
                <Brain className="w-3 h-3" /> AI Evaluator
              </div>
            </div>
          )}
        </motion.div>

        {/* ── Main Score Grid ── */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
          {[
            { icon: Target, label: "Overall Score", value: `${overallScore}/100`, color: overallScore >= 70 ? "emerald" : overallScore >= 40 ? "amber" : "rose" },
            { icon: Code2, label: "Coding Ability", value: `${codingScore}/100`, color: "indigo" },
            { icon: MessageSquare, label: "AI Interview", value: `${interviewScore}/100`, color: "purple" },
          ].map((card, i) => (
            <div key={i} className={`rounded-3xl border p-6 text-center bg-${card.color}-500/5 border-${card.color}-500/15`}
              style={{ backgroundColor: `color-mix(in srgb, var(--tw-${card.color}) 5%, transparent)` }}>
              <card.icon className={`w-6 h-6 mx-auto mb-3 text-${card.color}-400`} />
              <div className="text-3xl font-bold mb-1">{card.value}</div>
              <div className="text-[11px] text-slate-500 uppercase font-bold tracking-wider">{card.label}</div>
            </div>
          ))}
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-10">
          {/* ── Left: Strengths & Improvements ── */}
          <div className="md:col-span-1 space-y-6">
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
              className="rounded-3xl border border-white/5 bg-white/2 p-6">
              <h3 className="text-sm font-bold flex items-center gap-2 mb-4 text-emerald-400">
                <TrendingUp className="w-4 h-4" /> Focus Topics
              </h3>
              <ul className="space-y-3">
                {report?.focus_topics?.map((s: string, i: number) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <Zap className="w-4 h-4 text-emerald-500/50 shrink-0 mt-0.5" />
                    <span>{s}</span>
                  </li>
                )) || <li className="text-sm text-slate-500">N/A</li>}
              </ul>
            </motion.div>

            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}
              className="rounded-3xl border border-white/5 bg-white/2 p-6">
              <h3 className="text-sm font-bold flex items-center gap-2 mb-4 text-amber-400">
                <ListTodo className="w-4 h-4" /> Actionable Feedback
              </h3>
              <ul className="space-y-3">
                {(report?.actionable_feedback || report?.improvements)?.map((s: string, i: number) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <Target className="w-4 h-4 text-amber-500/50 shrink-0 mt-0.5" />
                    <span>{s}</span>
                  </li>
                )) || <li className="text-sm text-slate-500">N/A</li>}
              </ul>
            </motion.div>
          </div>

          {/* ── Right: Question Breakdown ── */}
          <div className="md:col-span-2">
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}>
              <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-400" /> Question Breakdown
              </h2>
              <div className="space-y-4">
                {perfs.map((p: any, i: number) => (
                  <div key={i} className={`rounded-2xl border p-5 ${
                      p.status === "accepted" ? "bg-emerald-500/5 border-emerald-500/15"
                      : p.status === "wrong_answer" ? "bg-rose-500/5 border-rose-500/15"
                      : "bg-white/5 border-white/10"
                    }`}>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        {statusIcon(p.status)}
                        <div>
                          <div className="font-bold text-sm">{p.question?.title || `Question ${i + 1}`}</div>
                          <div className="text-[10px] text-slate-500 uppercase mt-0.5">
                            {p.status === "accepted" ? "Solved" : p.status === "wrong_answer" ? "Wrong Answer" : "Skipped"} 
                            <span className="mx-1.5">•</span> {p.language} 
                            <span className="mx-1.5">•</span> {p.attempts} attempt{p.attempts !== 1 ? "s" : ""}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-black/20 px-2.5 py-1 rounded-lg">
                        <Clock className="w-3 h-3" />{formatTime(p.time_spent)}
                      </div>
                    </div>
                    {p.interview_brief && (
                      <div className="bg-black/20 rounded-xl p-3 text-xs text-slate-400 leading-relaxed mt-3 border border-white/5">
                        <div className="text-[10px] text-purple-400 font-bold uppercase mb-1.5 flex items-center gap-1">
                          <MessageSquare className="w-3 h-3" /> AI Interview Snippet
                        </div>
                        {p.interview_brief.split("\n").slice(0, 4).map((line: string, j: number) => (
                          <p key={j} className="mb-0.5 line-clamp-1">{line}</p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>

        {/* ── Actions ── */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="mt-8 text-center pb-12">
          <Link href="/start-interview"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40 transition-all">
            Start Another Interview
          </Link>
        </motion.div>
      </div>
    </div>
  );
}

