"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, CheckCircle, List, MessageSquare } from "lucide-react";
import { api } from "@/lib/api";
import type { OnboardingProgress, TextbookContent, QuizSet } from "@/types";
import { ProgressRingStacked } from "@/components/onboarding/ProgressRing";

export default function OnboardingHome() {
  const [progress, setProgress] = useState<OnboardingProgress | null>(null);
  const [textbook, setTextbook] = useState<TextbookContent | null>(null);
  const [quizzes, setQuizzes] = useState<QuizSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [contentReady, setContentReady] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<OnboardingProgress>("/api/onboarding/progress"),
      api.get<TextbookContent>("/api/onboarding/textbook").catch(() => null),
      api.get<QuizSet[]>("/api/onboarding/quizzes").catch(() => []),
    ])
      .then(([prog, tb, qz]) => {
        setProgress(prog);
        setTextbook(tb);
        setQuizzes(qz ?? []);
        setContentReady(!!tb);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="w-8 h-8 border-2 border-[#1E2D4A] border-t-[#C9A84C] rounded-full animate-spin" />
      </div>
    );
  }

  if (!contentReady) {
    return (
      <div className="text-center py-20 space-y-3">
        <div className="w-8 h-8 border-2 border-[#1E2D4A] border-t-[#C9A84C] rounded-full animate-spin mx-auto" />
        <p className="text-[#64748B]">Content being prepared…</p>
      </div>
    );
  }

  const totalChapters = textbook?.chapters.length ?? 0;
  const chaptersRead = progress?.chapters_read.length ?? 0;
  const textbookPct = totalChapters > 0 ? (chaptersRead / totalChapters) * 100 : 0;

  const chapterQuizzes = quizzes.filter((q) => q.quiz_type !== "final_assessment");
  const quizzesDone = progress?.quizzes_completed.length ?? 0;
  const quizPct = chapterQuizzes.length > 0 ? (quizzesDone / chapterQuizzes.length) * 100 : 0;

  const allChapterQuizzesDone = chapterQuizzes.length > 0 && quizzesDone >= chapterQuizzes.length;
  const firstUnreadChapter = textbook?.chapters.find(
    (ch) => !progress?.chapters_read.includes(ch.chapter_index),
  );

  return (
    <div className="max-w-4xl space-y-10">
      <div>
        <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE] mb-1">
          Welcome back
        </h1>
        <p className="text-[#64748B]">Your legal onboarding progress</p>
      </div>

      <div className="flex gap-8 items-center">
        <ProgressRingStacked percentage={textbookPct} label="Textbook" />
        <ProgressRingStacked percentage={quizPct} label="Quizzes" />
        <div className="flex flex-col items-center gap-2">
          <div className="w-24 h-24 rounded-full border-4 border-[#1E2D4A] flex items-center justify-center">
            <span className="font-[family-name:var(--font-playfair)] text-xl font-semibold text-[#F5F3EE]">
              {progress?.checklist_uses ?? 0}
            </span>
          </div>
          <span className="text-xs text-[#64748B]">Checklist uses</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <NavCard
          href="/onboarding/textbook"
          icon={<BookOpen size={20} className="text-[#C9A84C]" />}
          title="Textbook"
          subtitle={`Chapter ${chaptersRead} of ${totalChapters}`}
          cta="Continue Reading"
          ctaHref={
            firstUnreadChapter
              ? "/onboarding/textbook"
              : "/onboarding/textbook"
          }
        />

        <NavCard
          href="/onboarding/quiz"
          icon={<CheckCircle size={20} className="text-[#C9A84C]" />}
          title="Quizzes"
          subtitle={`${quizzesDone} of ${chapterQuizzes.length} complete`}
          cta={allChapterQuizzesDone ? "Take Final Assessment" : "Continue"}
          badge={allChapterQuizzesDone ? "Final Assessment" : undefined}
          ctaHref="/onboarding/quiz"
        />

        <NavCard
          href="/onboarding/checklist"
          icon={<List size={20} className="text-[#C9A84C]" />}
          title="Contract Checklist"
          subtitle="Review any contract against your org's standards"
          cta="Open Checklist"
          ctaHref="/onboarding/checklist"
        />

        <NavCard
          href="/onboarding/chat"
          icon={<MessageSquare size={20} className="text-[#C9A84C]" />}
          title="Ask the Playbook"
          subtitle="Your org's contract knowledge, on demand"
          cta="Start Chatting"
          ctaHref="/onboarding/chat"
        />
      </div>
    </div>
  );
}

function NavCard({
  href,
  icon,
  title,
  subtitle,
  cta,
  ctaHref,
  badge,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  cta: string;
  ctaHref: string;
  badge?: string;
}) {
  return (
    <div className="bg-[#1A2540] border border-[#1E2D4A] rounded-lg p-5 space-y-4 hover:border-[#C9A84C]/30 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {icon}
          <div>
            <p className="font-semibold text-[#F5F3EE]">{title}</p>
            <p className="text-xs text-[#64748B] mt-0.5">{subtitle}</p>
          </div>
        </div>
        {badge && (
          <span className="text-[10px] font-semibold text-[#C9A84C] border border-[#C9A84C]/40 px-2 py-0.5 rounded-full uppercase tracking-wider">
            {badge}
          </span>
        )}
      </div>
      <Link
        href={ctaHref}
        className="block text-center text-sm font-semibold bg-[#C9A84C] text-[#0F1729] py-2 rounded hover:bg-[#B8963E] transition-colors"
      >
        {cta}
      </Link>
    </div>
  );
}
