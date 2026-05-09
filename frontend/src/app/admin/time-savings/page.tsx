"use client";

import { useState } from "react";
import { Clock, CheckSquare, Square } from "lucide-react";

type Category = "Textbook" | "Quiz" | "Final Assessment" | "Checklist";

interface ReviewItem {
  id: number;
  label: string;
  category: Category;
  minutes: number;
}

// 10 textbook chapters (240 min) + 8 chapter quizzes (200 min) +
// 1 final assessment (60 min) + 1 contract checklist (100 min) = 600 min
const REVIEW_ITEMS: ReviewItem[] = [
  { id: 1,  label: "Textbook — Chapter 1: Introduction & Contract Framework",  category: "Textbook",          minutes: 20 },
  { id: 2,  label: "Textbook — Chapter 2: Clause Coverage",                    category: "Textbook",          minutes: 25 },
  { id: 3,  label: "Textbook — Chapter 3: Clause Coverage",                    category: "Textbook",          minutes: 25 },
  { id: 4,  label: "Textbook — Chapter 4: Clause Coverage",                    category: "Textbook",          minutes: 25 },
  { id: 5,  label: "Textbook — Chapter 5: Clause Coverage",                    category: "Textbook",          minutes: 25 },
  { id: 6,  label: "Textbook — Chapter 6: Clause Coverage",                    category: "Textbook",          minutes: 25 },
  { id: 7,  label: "Textbook — Chapter 7: Clause Coverage",                    category: "Textbook",          minutes: 25 },
  { id: 8,  label: "Textbook — Chapter 8: Clause Coverage",                    category: "Textbook",          minutes: 25 },
  { id: 9,  label: "Textbook — Chapter 9: Clause Coverage",                    category: "Textbook",          minutes: 25 },
  { id: 10, label: "Textbook — Chapter 10: Red Flags Summary",                 category: "Textbook",          minutes: 20 },
  { id: 11, label: "Chapter Quiz 1 — Questions & Answer Key",                  category: "Quiz",              minutes: 25 },
  { id: 12, label: "Chapter Quiz 2 — Questions & Answer Key",                  category: "Quiz",              minutes: 25 },
  { id: 13, label: "Chapter Quiz 3 — Questions & Answer Key",                  category: "Quiz",              minutes: 25 },
  { id: 14, label: "Chapter Quiz 4 — Questions & Answer Key",                  category: "Quiz",              minutes: 25 },
  { id: 15, label: "Chapter Quiz 5 — Questions & Answer Key",                  category: "Quiz",              minutes: 25 },
  { id: 16, label: "Chapter Quiz 6 — Questions & Answer Key",                  category: "Quiz",              minutes: 25 },
  { id: 17, label: "Chapter Quiz 7 — Questions & Answer Key",                  category: "Quiz",              minutes: 25 },
  { id: 18, label: "Chapter Quiz 8 — Questions & Answer Key",                  category: "Quiz",              minutes: 25 },
  { id: 19, label: "Final Assessment — Comprehensive Knowledge Check",          category: "Final Assessment",  minutes: 60 },
  { id: 20, label: "Contract Checklist — All Categories & Risk Items",          category: "Checklist",         minutes: 100 },
];

const TOTAL_ESTIMATE_MINUTES = 600;

// Pre-check Quiz 7, Quiz 8, Final Assessment → 25 + 25 + 60 = 110 min
const INITIAL_COMPLETED = new Set([17, 18, 19]);

const CATEGORY_STYLES: Record<Category, string> = {
  "Textbook":         "text-[#7B9FDB] bg-[#7B9FDB]/10",
  "Quiz":             "text-[#82C9A0] bg-[#82C9A0]/10",
  "Final Assessment": "text-[#C9A84C] bg-[#C9A84C]/10",
  "Checklist":        "text-[#C97B7B] bg-[#C97B7B]/10",
};

function formatMinutes(total: number): string {
  if (total < 60) return `${total} min`;
  const hours = Math.floor(total / 60);
  const mins = total % 60;
  return mins === 0 ? `${hours} hr` : `${hours} hr ${mins} min`;
}

export default function TimeSavingsPage() {
  const [completedIds, setCompletedIds] = useState<Set<number>>(
    new Set(INITIAL_COMPLETED)
  );

  function toggle(id: number) {
    setCompletedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  const savedMinutes = REVIEW_ITEMS.filter((i) => completedIds.has(i.id)).reduce(
    (sum, i) => sum + i.minutes,
    0
  );
  const progressPct = Math.min(
    100,
    Math.round((savedMinutes / TOTAL_ESTIMATE_MINUTES) * 100)
  );

  return (
    <div className="space-y-8 max-w-3xl">
      <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE]">
        Time Savings
      </h1>

      {/* Banner */}
      <div className="bg-[#1A2540] border border-[#1E2D4A] rounded-lg px-6 py-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Clock size={20} className="text-[#C9A84C]" />
            <span className="text-[#8899BB] text-sm uppercase tracking-wider font-semibold">
              Estimated time saved this contract
            </span>
          </div>
          <span className="text-[#64748B] text-sm">
            of {formatMinutes(TOTAL_ESTIMATE_MINUTES)} estimated manual review
          </span>
        </div>

        <div className="flex items-end gap-3">
          <span className="font-[family-name:var(--font-playfair)] text-5xl font-semibold text-[#C9A84C]">
            {formatMinutes(savedMinutes)}
          </span>
          <span className="text-[#64748B] text-sm mb-2">saved</span>
        </div>

        <div className="space-y-1">
          <div className="w-full h-2 bg-[#0F1729] rounded-full overflow-hidden">
            <div
              className="h-full bg-[#C9A84C] rounded-full transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-[#64748B]">
            <span>{progressPct}% of manual effort automated</span>
            <span>
              {completedIds.size} / {REVIEW_ITEMS.length} items reviewed
            </span>
          </div>
        </div>
      </div>

      {/* Review Queue */}
      <section>
        <h2 className="font-[family-name:var(--font-playfair)] text-xl font-semibold text-[#F5F3EE] mb-4">
          Review Queue
        </h2>

        <div className="space-y-2">
          {REVIEW_ITEMS.map((item) => {
            const done = completedIds.has(item.id);
            const pillClass = CATEGORY_STYLES[item.category];
            return (
              <button
                key={item.id}
                onClick={() => toggle(item.id)}
                className={[
                  "w-full flex items-center gap-4 px-4 py-3.5 rounded-md border text-left transition-colors",
                  done
                    ? "bg-[#1A2540] border-[#C9A84C]/30"
                    : "bg-[#0F1729] border-[#1E2D4A] hover:bg-[#131E33]",
                ].join(" ")}
              >
                {done ? (
                  <CheckSquare size={18} className="text-[#C9A84C] shrink-0" />
                ) : (
                  <Square size={18} className="text-[#64748B] shrink-0" />
                )}
                <span
                  className={[
                    "flex-1 text-sm",
                    done ? "text-[#8899BB] line-through" : "text-[#F5F3EE]",
                  ].join(" ")}
                >
                  {item.label}
                </span>
                <span
                  className={[
                    "hidden sm:inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0",
                    pillClass,
                  ].join(" ")}
                >
                  {item.category}
                </span>
                <span className="text-xs text-[#64748B] shrink-0 w-12 text-right">
                  {item.minutes} min
                </span>
              </button>
            );
          })}
        </div>
      </section>

      {/* Callout */}
      <div className="bg-[#0F1729] border border-[#1E2D4A] rounded-md px-5 py-4">
        <p className="text-xs text-[#64748B] leading-relaxed">
          Time estimates reflect average manual effort to draft and verify each piece of onboarding
          content from scratch. Mark an item complete once you have reviewed the AI-generated
          output and confirmed its accuracy.
        </p>
      </div>
    </div>
  );
}
