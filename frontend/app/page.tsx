"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { questionApi, authApi } from "@/lib/api";
import { motion } from "framer-motion";
import { Brain, Code2, Sparkles, TrendingUp, ArrowRight, User as UserIcon, LogOut, Flame } from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const [questions, setQuestions] = useState<any[]>([]);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const router = useRouter();

  useEffect(() => {
    // Fetch user profile
    authApi.getCurrentUser()
      .then(res => setUser(res.data))
      .catch(err => console.error("Failed to fetch user", err));

    // Fetch recommendations
    questionApi.getRecommendations()
      .then((res) => setQuestions(res.data))
      .catch((err) => {
        console.error(err);
        if (err.response && (err.response.status === 401 || err.response.status === 403)) {
          router.push("/login");
        }
      })
      .finally(() => setLoading(false));
  }, [router]);

  const handleLogout = async () => {
    try {
      await authApi.logout();
      router.push("/login");
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-6 md:py-12">
      {/* ── Topbar (Profile & Logout) ── */}
      <div className="flex justify-end mb-8">
        {user ? (
          <div className="flex items-center gap-4 bg-white/5 border border-white/10 rounded-2xl p-2 pr-4 shadow-lg">
            <Link href="/profile" className="flex items-center gap-3 hover:bg-white/5 p-1.5 pr-3 rounded-xl transition-colors group">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30 group-hover:bg-indigo-500/30 transition-colors">
                <UserIcon className="w-5 h-5" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-slate-200 leading-tight group-hover:text-indigo-300 transition-colors">{user.username}</span>
                <div className="flex items-center gap-1 mt-0.5">
                  <Flame className="w-3.5 h-3.5 text-amber-500" />
                  <span className="text-xs font-bold text-amber-500">{user.profile?.streak_count || 0} Day Streak</span>
                </div>
              </div>
            </Link>
            <div className="w-px h-8 bg-white/10 mx-1" />
            <Link href="/profile" className="text-slate-500 hover:text-indigo-400 transition-colors p-2 rounded-lg hover:bg-indigo-500/10" title="View Profile">
              <TrendingUp className="w-4 h-4" />
            </Link>
            <button onClick={handleLogout} className="text-slate-500 hover:text-rose-400 transition-colors p-2 rounded-lg hover:bg-rose-500/10" title="Logout">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="h-14" /> /* Placeholder */
        )}
      </div>

      {/* Hero Section */}
      <div className="mb-16 text-center">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-medium mb-6"
        >
          <Sparkles className="w-4 h-4" />
          AI-Powered DSA Mastery
        </motion.div>
        <h1 className="text-5xl md:text-6xl font-display font-bold mb-6 text-gradient">
          Ready for your next big <br /> interview?
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-8">
          Practice like it's the real thing. Solve trending DSA questions and face 
          follow-up questions from our AI interviewer.
        </p>
        <Link
          href="/start-interview"
          className="inline-flex items-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm transition-all shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40"
        >
          <Sparkles className="w-5 h-5" />
          Start Custom Interview
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Recommended Questions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="col-span-full flex items-center justify-between mb-2">
          <h2 className="text-2xl font-display font-semibold flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-purple-400" />
            Recommended for You
          </h2>
          <button className="text-indigo-400 text-sm font-medium hover:underline">View All</button>
        </div>

        {loading ? (
          [1, 2, 3].map((i) => (
            <div key={i} className="h-64 glass animate-pulse rounded-3xl" />
          ))
        ) : (
          questions.map((q, idx) => (
            <motion.div
              key={q.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              className="glass p-6 rounded-3xl group cursor-pointer hover:border-indigo-500/30 transition-all"
            >
              <div className="flex justify-between items-start mb-4">
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                  q.difficulty === 'Easy' ? 'bg-emerald-500/10 text-emerald-400' :
                  q.difficulty === 'Medium' ? 'bg-amber-500/10 text-amber-400' :
                  'bg-rose-500/10 text-rose-400'
                }`}>
                  {q.difficulty}
                </span>
                <Brain className="w-5 h-5 text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <h3 className="text-xl font-bold mb-3 group-hover:text-indigo-400 transition-colors">
                {q.title}
              </h3>
              <p className="text-slate-400 text-sm line-clamp-2 mb-6" title={q.description.replace(/<[^>]+>/g, '')}>
                {q.description.replace(/<[^>]+>/g, '')}
              </p>
              <div className="flex flex-wrap gap-2 mb-8">
                {q.companies.slice(0, 3).map((c: string) => (
                  <span key={c} className="text-[10px] px-2 py-0.5 rounded bg-white/5 border border-white/10 text-slate-500">
                    {c}
                  </span>
                ))}
              </div>
              <Link 
                href={`/interview/${q.id}`}
                className="w-full btn-primary flex items-center justify-center gap-2"
              >
                <Code2 className="w-4 h-4" />
                Practice Mock Interview
              </Link>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
