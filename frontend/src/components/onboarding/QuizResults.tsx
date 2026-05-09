"use client";

import { useState } from "react";
import { Check, X, ChevronDown, ChevronRight } from "lucide-react";
import type { Question } from "@/types";

interface QuizResultsProps {
  questions: Question[];
  answers: string[];
  quizId: string;
  onRetry: () => void;
  onNext?: () => void;
}

function matchesAnswer(selected: string, answer: string): boolean {
  return selected === answer || selected.startsWith(answer + ".") || selected.startsWith(answer + " ");
}

export function QuizResults({ questions, answers, onRetry, onNext }: QuizResultsProps) {
  const correct = answers.filter((a, i) => matchesAnswer(a, questions[i]?.correct_answer ?? "")).length;
  const total = questions.length;
  const passed = correct === total;

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="text-center space-y-3">
        <p className="font-[family-name:var(--font-playfair)] text-6xl font-semibold text-[#F5F3EE]">
          {correct}/{total}
        </p>

        {passed ? (
          <div className="inline-flex items-center gap-2 bg-green-900/30 border border-green-700/50 text-green-400 px-4 py-2 rounded-full text-sm font-semibold">
            <Check size={14} strokeWidth={3} />
            PASSED
          </div>
        ) : (
          <div className="inline-flex items-center gap-2 bg-amber-900/30 border border-amber-700/50 text-amber-400 px-4 py-2 rounded-full text-sm font-semibold">
            NOT YET
          </div>
        )}

        <p className="text-sm text-[#64748B]">
          {passed
            ? "Chapter mastered. Onboarding credit earned."
            : "You need 100% to complete this chapter. Review the chapter, then retake. You can retry as many times as needed."}
        </p>
      </div>

      <div className="space-y-2">
        {questions.map((q, i) => (
          <QuestionSummary
            key={i}
            question={q}
            userAnswer={answers[i] ?? ""}
            index={i}
          />
        ))}
      </div>

      <div className="flex gap-3">
        {passed ? (
          onNext && (
            <button
              onClick={onNext}
              className="flex-1 py-3 bg-[#C9A84C] text-[#0F1729] rounded-md font-semibold hover:bg-[#B8963E] transition-colors"
            >
              Next Chapter →
            </button>
          )
        ) : (
          <>
            <button
              onClick={onRetry}
              className="flex-1 py-3 bg-[#C9A84C] text-[#0F1729] rounded-md font-semibold hover:bg-[#B8963E] transition-colors"
            >
              Retry Quiz
            </button>
            <a
              href="/onboarding/textbook"
              className="flex-1 py-3 border border-[#1E2D4A] text-[#8899BB] rounded-md font-medium text-center hover:border-[#C9A84C]/50 hover:text-[#F5F3EE] transition-colors"
            >
              Back to Chapter
            </a>
          </>
        )}
      </div>
    </div>
  );
}

function QuestionSummary({
  question,
  userAnswer,
  index,
}: {
  question: Question;
  userAnswer: string;
  index: number;
}) {
  const [open, setOpen] = useState(false);
  const correct = matchesAnswer(userAnswer, question.correct_answer);

  return (
    <div className="border border-[#1E2D4A] rounded-md overflow-hidden">
      <button
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#1A2540] transition-colors"
      >
        <span
          className={[
            "w-6 h-6 rounded-full flex items-center justify-center shrink-0",
            correct ? "bg-green-900/40 text-green-400" : "bg-red-900/40 text-red-400",
          ].join(" ")}
        >
          {correct ? <Check size={12} strokeWidth={3} /> : <X size={12} strokeWidth={3} />}
        </span>
        <span className="flex-1 text-sm text-left text-[#F5F3EE] truncate">
          {index + 1}. {question.text}
        </span>
        {open ? (
          <ChevronDown size={14} className="text-[#64748B] shrink-0" />
        ) : (
          <ChevronRight size={14} className="text-[#64748B] shrink-0" />
        )}
      </button>

      {open && (
        <div className="px-4 pb-4 pt-2 border-t border-[#1E2D4A] space-y-2 text-sm">
          <p>
            <span className="text-[#64748B]">Your answer: </span>
            <span className={correct ? "text-green-400" : "text-red-400"}>{userAnswer || "—"}</span>
          </p>
          {!correct && (
            <p>
              <span className="text-[#64748B]">Correct: </span>
              <span className="text-green-400">
                {question.options.find((o) => matchesAnswer(o, question.correct_answer)) ?? question.correct_answer}
              </span>
            </p>
          )}
          <p className="text-[#8899BB] italic">{question.explanation}</p>
        </div>
      )}
    </div>
  );
}
