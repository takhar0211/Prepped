"use client";
import { useEffect, useState } from "react";
import { authApi } from "@/lib/api";
import { motion } from "framer-motion";
import { Trophy, Code2, Target, Brain, ArrowLeft, History, Clock } from "lucide-react";
import Link from "next/link";

export default function ProfilePage() {
  const [user, setUser] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      authApi.getCurrentUser(),
      authApi.getProfileStats()
    ])
      .then(([userRes, statsRes]) => {
        setUser(userRes.data);
        setStats(statsRes.data);
      })
      .catch(err => console.error("Failed to fetch profile stats", err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0a0a0f]">
        <div className="w-8 h-8 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
        <span className="ml-3 text-slate-400">Loading profile...</span>
      </div>
    );
  }

  if (!user || !stats) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0a0a0f] flex-col gap-4">
        <p className="text-slate-400">Please log in to view your profile.</p>
        <Link href="/login" className="px-6 py-2 bg-indigo-600 rounded-lg text-white font-bold">Login</Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <Link href="/" className="inline-flex items-center gap-2 text-slate-500 hover:text-slate-300 text-sm mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>

        {/* ── Header ── */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-6 mb-12">
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border-2 border-indigo-500/30 flex items-center justify-center">
            <span className="text-4xl font-bold text-indigo-400 uppercase">{user.username[0]}</span>
          </div>
          <div>
            <h1 className="text-4xl font-bold mb-2">{user.username}</h1>
            <p className="text-slate-400 text-sm">
              <span className="text-amber-400 font-bold">{user.profile?.streak_count || 0} Day Streak</span>
              {user.profile?.leetcode_username && ` • LeetCode: ${user.profile.leetcode_username}`}
            </p>
          </div>
        </motion.div>

        {/* ── Stats Grid ── */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          {[
            { icon: Target, label: "Questions Attempted", value: stats.questions.attempted, color: "slate" },
            { icon: Code2, label: "Questions Solved", value: stats.questions.solved, color: "emerald" },
            { icon: Brain, label: "Mocks Attempted", value: stats.mocks.attempted, color: "amber" },
            { icon: Trophy, label: "Mocks Completed", value: stats.mocks.completed, color: "indigo" },
          ].map((card, i) => (
            <div key={i} className={`rounded-3xl border p-6 text-center bg-${card.color}-500/5 border-${card.color}-500/15`}
              style={{ backgroundColor: card.color === "slate" ? "rgba(255,255,255,0.02)" : `color-mix(in srgb, var(--tw-${card.color}) 5%, transparent)` }}>
              <card.icon className={`w-6 h-6 mx-auto mb-3 text-${card.color}-400`} />
              <div className="text-3xl font-bold mb-1">{card.value}</div>
              <div className="text-[11px] text-slate-500 uppercase font-bold tracking-wider">{card.label}</div>
            </div>
          ))}
        </motion.div>

        {/* ── Recent Mocks ── */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <History className="w-5 h-5 text-purple-400" /> Recent Mock Interviews
          </h2>
          
          {stats.recent_history.length === 0 ? (
            <div className="rounded-3xl border border-white/5 bg-white/2 p-8 text-center text-slate-400 text-sm">
              You haven't attempted any mock interviews yet.
            </div>
          ) : (
            <div className="space-y-4">
              {stats.recent_history.map((mock: any, i: number) => (
                <Link href={mock.status === "completed" ? `/results/${mock.id}` : `/interview/${mock.resume_question_id}?mock=${mock.id}`} key={i}
                  className="block rounded-2xl border border-white/5 bg-white/2 p-5 hover:bg-white/5 hover:border-white/10 transition-all group">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                        mock.status === "completed" ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400"
                      }`}>
                        {mock.status === "completed" ? <Trophy className="w-5 h-5" /> : <Clock className="w-5 h-5" />}
                      </div>
                      <div>
                        <h3 className="font-bold capitalize">{mock.topic.replace("_", " ")} Mock</h3>
                        <p className="text-xs text-slate-500 mt-1">
                          {mock.difficulty} • {new Date(mock.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      {mock.status === "completed" ? (
                        <div>
                          <div className="text-lg font-bold text-emerald-400">{mock.score}/100</div>
                          <div className="text-[10px] text-slate-500 uppercase font-bold">Score</div>
                        </div>
                      ) : (
                        <div className="text-xs font-bold text-amber-400 uppercase px-3 py-1 bg-amber-500/10 rounded-lg">
                          In Progress
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </motion.div>

      </div>
    </div>
  );
}
