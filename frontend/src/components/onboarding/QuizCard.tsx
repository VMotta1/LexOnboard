"use client";

import { useState } from "react";
import { Check, X, Lightbulb } from "lucide-react";
import type { Question } from "@/types";

interface QuizCardProps {
  question: Question;
  questionNumber: number;
  total: number;
  quizType: string;
  onAnswer: (selected: string, correct: boolean) => void;
  onNext: () => void;
}

const OPTION_LABELS = ["A", "B", "C", "D"];

// Options may be "A. full text" while correct_answer is just "A"
function matchesAnswer(option: string, answer: string): boolean {
  return option === answer || option.startsWith(answer + ".") || option.startsWith(answer + " ");
}

export function QuizCard({ question, questionNumber, total, quizType, onAnswer, onNext }: QuizCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [answered, setAnswered] = useState(false);

  function handleSelect(option: string) {
    if (answered) return;
    setSelected(option);
    setAnswered(true);
    onAnswer(option, matchesAnswer(option, question.correct_answer));
  }

  const isTrueFalse = question.options.length === 2 &&
    question.options.every((o) => ["True", "False"].includes(o));

  const isCorrect = selected !== null && matchesAnswer(selected, question.correct_answer);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-[#C9A84C] uppercase tracking-wider px-2 py-1 border border-[#C9A84C]/30 rounded">
          {quizType.replace(/_/g, " ")}
        </span>
        <span className="text-sm text-[#64748B]">
          {questionNumber} / {total}
        </span>
      </div>

      <p className="text-lg font-medium text-[#F5F3EE] leading-snug">{question.text}</p>

      {isTrueFalse ? (
        <div className="flex gap-4">
          {question.options.map((option) => (
            <TFButton
              key={option}
              option={option}
              selected={selected}
              correct={question.correct_answer}
              answered={answered}
              onSelect={handleSelect}
            />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {question.options.map((option, i) => (
            <MCQButton
              key={i}
              option={option}
              label={OPTION_LABELS[i] ?? String(i + 1)}
              selected={selected}
              correct={question.correct_answer}
              answered={answered}
              onSelect={handleSelect}
            />
          ))}
        </div>
      )}

      {answered && (
        <div className="border border-[#C9A84C]/20 rounded-lg p-4 bg-[#C9A84C]/5 space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
          <div className="flex items-center gap-2">
            <Lightbulb size={14} className="text-[#C9A84C]" />
            <span className="text-xs font-semibold text-[#C9A84C] uppercase tracking-wider">
              {isCorrect ? "Correct" : `Correct answer: ${question.options.find((o) => matchesAnswer(o, question.correct_answer)) ?? question.correct_answer}`}
            </span>
          </div>
          <p className="text-sm text-[#8899BB]">{question.explanation}</p>
        </div>
      )}

      {answered && (
        <button
          onClick={onNext}
          className="w-full py-3 bg-[#C9A84C] text-[#0F1729] rounded-md font-semibold hover:bg-[#B8963E] transition-colors"
        >
          Next Question →
        </button>
      )}
    </div>
  );
}

function optionStyles(option: string, selected: string | null, correct: string, answered: boolean) {
  if (!answered) return "border-[#1E2D4A] text-[#F5F3EE] hover:border-[#C9A84C]/50";
  if (matchesAnswer(option, correct)) return "border-green-500 bg-green-900/20 text-[#F5F3EE]";
  if (option === selected && !matchesAnswer(option, correct)) return "border-red-500 bg-red-900/20 text-[#F5F3EE]";
  return "border-[#1E2D4A] text-[#64748B] opacity-50";
}

function MCQButton({
  option, label, selected, correct, answered, onSelect,
}: {
  option: string; label: string; selected: string | null;
  correct: string; answered: boolean; onSelect: (o: string) => void;
}) {
  const styles = optionStyles(option, selected, correct, answered);
  const isCorrect = matchesAnswer(option, correct) && answered;
  const isWrong = option === selected && !matchesAnswer(option, correct);

  return (
    <button
      onClick={() => onSelect(option)}
      disabled={answered}
      className={`w-full flex items-center gap-3 border rounded-md px-4 py-3 text-left transition-colors ${styles}`}
    >
      <span className="w-6 h-6 rounded border border-current flex items-center justify-center text-xs font-semibold shrink-0">
        {isCorrect ? <Check size={12} strokeWidth={3} /> : isWrong ? <X size={12} strokeWidth={3} /> : label}
      </span>
      <span className="text-sm">{option}</span>
    </button>
  );
}

function TFButton({
  option, selected, correct, answered, onSelect,
}: {
  option: string; selected: string | null; correct: string; answered: boolean; onSelect: (o: string) => void;
}) {
  const styles = optionStyles(option, selected, correct, answered);
  return (
    <button
      onClick={() => onSelect(option)}
      disabled={answered}
      className={`flex-1 py-4 border rounded-md font-semibold transition-colors ${styles}`}
    >
      {option}
    </button>
  );
}
