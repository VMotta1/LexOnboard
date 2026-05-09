"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle } from "lucide-react";
import { api } from "@/lib/api";
import type { QuizSet, OnboardingProgress } from "@/types";

export default function QuizIndexPage() {
  const [quizzes, setQuizzes] = useState<QuizSet[]>([]);
  const [progress, setProgress] = useState<OnboardingProgress | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<QuizSet[]>("/api/onboarding/quizzes"),
      api.get<OnboardingProgress>("/api/onboarding/progress"),
    ])
      .then(([qz, prog]) => {
        setQuizzes(qz);
        setProgress(prog);
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

  const chapterQuizzes = quizzes.filter((q) => q.quiz_type !== "final_assessment");
  const finalAssessment = quizzes.find((q) => q.quiz_type === "final_assessment");
  const allChaptersDone =
    chapterQuizzes.length > 0 &&
    chapterQuizzes.every((q) => progress?.quizzes_completed.includes(q.id));

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE] mb-2">
          Quizzes
        </h1>
        <p className="text-[#64748B]">
          {progress?.quizzes_completed.length ?? 0} of {chapterQuizzes.length} chapter quizzes completed
        </p>
      </div>

      <div className="space-y-3">
        <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider">Chapter Quizzes</p>
        {chapterQuizzes.map((quiz, i) => {
          const passed = progress?.quizzes_completed.includes(quiz.id);
          return (
            <Link
              key={quiz.id}
              href={`/onboarding/quiz/${quiz.id}`}
              className="flex items-center gap-4 bg-[#1A2540] border border-[#1E2D4A] rounded-lg px-4 py-4 hover:border-[#C9A84C]/30 transition-colors"
            >
              <div
                className={[
                  "w-8 h-8 rounded-full flex items-center justify-center",
                  passed ? "bg-[#C9A84C]/20 text-[#C9A84C]" : "bg-[#0D1829] text-[#64748B]",
                ].join(" ")}
              >
                {passed ? <CheckCircle size={16} /> : <span className="text-sm font-semibold">{i + 1}</span>}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-[#F5F3EE]">
                  {quiz.quiz_type.replace(/_/g, " ")}
                </p>
                <p className="text-xs text-[#64748B]">{quiz.questions.length} questions</p>
              </div>
              <span className={`text-xs font-semibold ${passed ? "text-green-400" : "text-[#64748B]"}`}>
                {passed ? "Passed" : "Start →"}
              </span>
            </Link>
          );
        })}
      </div>

      {finalAssessment && (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider">Final Assessment</p>
          <div className={`relative ${!allChaptersDone ? "opacity-50 pointer-events-none" : ""}`}>
            <Link
              href={`/onboarding/quiz/${finalAssessment.id}`}
              className="flex items-center gap-4 bg-[#1A2540] border border-[#C9A84C]/30 rounded-lg px-4 py-4 hover:border-[#C9A84C]/60 transition-colors"
            >
              <div className="w-8 h-8 rounded-full bg-[#C9A84C]/10 text-[#C9A84C] flex items-center justify-center">
                ★
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-[#F5F3EE]">Final Assessment</p>
                <p className="text-xs text-[#64748B]">
                  {finalAssessment.questions.length} questions · Covers all chapters
                </p>
              </div>
              <span className="text-xs font-semibold text-[#C9A84C]">
                {allChaptersDone ? "Take →" : "Complete all chapters first"}
              </span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
