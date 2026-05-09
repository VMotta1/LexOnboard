"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { QuizSet, Question, OnboardingProgress } from "@/types";
import { QuizCard } from "@/components/onboarding/QuizCard";
import { QuizResults } from "@/components/onboarding/QuizResults";

type Phase = "intro" | "question" | "results";

function shuffle<T>(arr: T[]): T[] {
  return [...arr].sort(() => Math.random() - 0.5);
}

export default function QuizPage() {
  const { id } = useParams<{ id: string }>();
  const [allQuizzes, setAllQuizzes] = useState<QuizSet[]>([]);
  const [quiz, setQuiz] = useState<QuizSet | null>(null);
  const [shuffled, setShuffled] = useState<Question[]>([]);
  const [phase, setPhase] = useState<Phase>("intro");
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<string[]>([]);
  const [pendingSelected, setPendingSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<QuizSet[]>("/api/onboarding/quizzes")
      .then((data) => {
        setAllQuizzes(data);
        const found = data.find((q) => q.id === id) ?? null;
        setQuiz(found);
        if (found) setShuffled(shuffle(found.questions));
      })
      .finally(() => setLoading(false));
  }, [id]);

  function handleAnswer(selected: string, _correct: boolean) {
    setPendingSelected(selected);
  }

  function handleNext() {
    const selected = pendingSelected ?? "";
    const newAnswers = [...answers, selected];
    setAnswers(newAnswers);
    setPendingSelected(null);

    if (currentQ < shuffled.length - 1) {
      setCurrentQ((p) => p + 1);
    } else {
      submitScore(newAnswers);
      setPhase("results");
    }
  }

  async function submitScore(finalAnswers: string[]) {
    if (!quiz) return;
    const correctCount = finalAnswers.filter((a, i) => {
      const ans = shuffled[i]?.correct_answer ?? "";
      return a === ans || a.startsWith(ans + ".") || a.startsWith(ans + " ");
    }).length;
    const score = correctCount / shuffled.length;
    try {
      await api.patch<OnboardingProgress>("/api/onboarding/progress", {
        quiz_score: { quiz_id: quiz.id, score },
      });
    } catch {
      // best-effort
    }
  }

  function handleRetry() {
    setShuffled(shuffle(quiz?.questions ?? []));
    setAnswers([]);
    setPendingSelected(null);
    setCurrentQ(0);
    setPhase("question");
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="w-8 h-8 border-2 border-[#1E2D4A] border-t-[#C9A84C] rounded-full animate-spin" />
      </div>
    );
  }

  if (!quiz) {
    return <p className="text-[#64748B] text-center py-20">Quiz not found.</p>;
  }

  const currentQuizIndex = allQuizzes.findIndex((q) => q.id === id);
  const nextQuiz = allQuizzes[currentQuizIndex + 1];

  if (phase === "intro") {
    return (
      <div className="max-w-xl mx-auto text-center space-y-6 py-20">
        <p className="text-xs font-semibold text-[#C9A84C] uppercase tracking-widest">
          {quiz.quiz_type.replace(/_/g, " ")}
        </p>
        <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE]">
          Ready to test your knowledge?
        </h1>
        <div className="flex justify-center gap-6 text-sm text-[#64748B]">
          <span>{quiz.questions.length} questions</span>
          <span>~{quiz.questions.length} min</span>
        </div>
        <button
          onClick={() => setPhase("question")}
          className="w-full max-w-xs py-3 bg-[#C9A84C] text-[#0F1729] rounded-md font-semibold hover:bg-[#B8963E] transition-colors"
        >
          Start Quiz
        </button>
      </div>
    );
  }

  if (phase === "question") {
    const q = shuffled[currentQ];
    if (!q) return null;
    return (
      <QuizCard
        key={currentQ}
        question={q}
        questionNumber={currentQ + 1}
        total={shuffled.length}
        quizType={quiz.quiz_type}
        onAnswer={handleAnswer}
        onNext={handleNext}
      />
    );
  }

  return (
    <QuizResults
      questions={shuffled}
      answers={answers}
      quizId={quiz.id}
      onRetry={handleRetry}
      onNext={
        nextQuiz
          ? () => window.location.assign(`/onboarding/quiz/${nextQuiz.id}`)
          : undefined
      }
    />
  );
}
