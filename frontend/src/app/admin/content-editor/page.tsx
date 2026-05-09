"use client";

import { useEffect, useState, useCallback } from "react";
import { ChevronDown, ChevronRight, RefreshCw, Save } from "lucide-react";
import { api, contentEditorApi, ApiError } from "@/lib/api";
import type {
  QuizSet,
  Question,
  ContractChecklist,
  ChecklistCategory,
  ChecklistItem,
} from "@/types";

// API returns chapter_number (not chapter_index) — define locally to match wire format
interface ApiChapter {
  chapter_number: number;
  title: string;
  content: string;
  key_takeaways: string[];
}

interface ApiTextbook {
  id: string;
  chapters: ApiChapter[];
  page_estimate: number;
  generated_at: string;
}

const GENERATION_ERROR = "_Content unavailable — generation error._";

type Tab = "textbook" | "quizzes" | "final" | "checklist";

const TABS: { id: Tab; label: string }[] = [
  { id: "textbook", label: "Textbook" },
  { id: "quizzes", label: "Quizzes" },
  { id: "final", label: "Final Assessment" },
  { id: "checklist", label: "Checklist" },
];

export default function ContentEditorPage() {
  const [activeTab, setActiveTab] = useState<Tab>("textbook");

  return (
    <div className="space-y-6 max-w-4xl">
      <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE]">
        Content Editor
      </h1>

      {/* Tabs */}
      <div className="flex border-b border-[#1E2D4A]">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={[
              "px-5 py-3 text-sm font-medium transition-colors -mb-px border-b-2",
              activeTab === tab.id
                ? "border-[#C9A84C] text-[#C9A84C]"
                : "border-transparent text-[#64748B] hover:text-[#8899BB]",
            ].join(" ")}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === "textbook" && <TextbookEditor />}
        {activeTab === "quizzes" && <QuizEditor quizType="chapter_review" />}
        {activeTab === "final" && <QuizEditor quizType="final_assessment" />}
        {activeTab === "checklist" && <ChecklistEditor />}
      </div>
    </div>
  );
}

/* ── Textbook ──────────────────────────────────────────────── */

function TextbookEditor() {
  const [textbook, setTextbook] = useState<ApiTextbook | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dirtyChapters, setDirtyChapters] = useState<Set<number>>(new Set());
  const [savingChapter, setSavingChapter] = useState<number | null>(null);
  const [regeneratingChapter, setRegeneratingChapter] = useState<number | null>(null);
  const [expandedChapters, setExpandedChapters] = useState<Set<number>>(new Set());

  useEffect(() => {
    api
      .get<ApiTextbook>("/api/onboarding/textbook")
      .then((data) => setTextbook(data))
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Failed to load textbook");
      })
      .finally(() => setLoading(false));
  }, []);

  function toggleChapter(num: number) {
    setExpandedChapters((prev) => {
      const next = new Set(prev);
      if (next.has(num)) {
        next.delete(num);
      } else {
        next.add(num);
      }
      return next;
    });
  }

  function updateChapterContent(chapterNumber: number, content: string) {
    if (!textbook) return;
    setTextbook({
      ...textbook,
      chapters: textbook.chapters.map((ch) =>
        ch.chapter_number === chapterNumber ? { ...ch, content } : ch
      ),
    });
    setDirtyChapters((prev) => new Set(prev).add(chapterNumber));
  }

  async function saveChapter(chapter: ApiChapter) {
    setSavingChapter(chapter.chapter_number);
    try {
      await contentEditorApi.saveChapter(chapter.chapter_number, chapter.content);
      setDirtyChapters((prev) => {
        const next = new Set(prev);
        next.delete(chapter.chapter_number);
        return next;
      });
    } finally {
      setSavingChapter(null);
    }
  }

  async function regenerateChapter(chapterNumber: number) {
    setRegeneratingChapter(chapterNumber);
    try {
      const res = await api.post<{ chapter: ApiChapter }>(
        "/api/onboarding/textbook/regenerate-chapter",
        { chapter_number: chapterNumber }
      );
      setTextbook((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          chapters: prev.chapters.map((ch) =>
            ch.chapter_number === chapterNumber ? res.chapter : ch
          ),
        };
      });
    } catch (err) {
      alert(err instanceof ApiError ? err.message : "Regeneration failed");
    } finally {
      setRegeneratingChapter(null);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!textbook) return <EmptyState message="No textbook generated yet." />;

  return (
    <div className="space-y-3">
      {textbook.chapters.map((chapter) => {
        const num = chapter.chapter_number;
        const expanded = expandedChapters.has(num);
        const dirty = dirtyChapters.has(num);
        const saving = savingChapter === num;
        const regenerating = regeneratingChapter === num;
        const isError = chapter.content === GENERATION_ERROR;
        // intro (0) and red flags (last) are hardcoded — only section chapters can be regenerated
        const canRegenerate = isError && num > 0 && num < textbook.chapters.length - 1;

        return (
          <div
            key={num}
            className={[
              "bg-[#1A2540] border rounded-lg overflow-hidden",
              isError ? "border-red-900/50" : "border-[#1E2D4A]",
            ].join(" ")}
          >
            <button
              onClick={() => toggleChapter(num)}
              className="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-[#131E33] transition-colors"
            >
              {expanded ? (
                <ChevronDown size={16} className="text-[#64748B] shrink-0" />
              ) : (
                <ChevronRight size={16} className="text-[#64748B] shrink-0" />
              )}
              <span className="text-xs text-[#64748B] font-semibold uppercase tracking-wider w-16 shrink-0">
                Ch. {num + 1}
              </span>
              <span className="flex-1 text-sm text-[#F5F3EE] font-medium">
                {chapter.title}
              </span>
              {isError && (
                <span className="w-2 h-2 rounded-full bg-red-500 shrink-0" title="Generation error — expand to regenerate" />
              )}
              {dirty && !isError && (
                <span className="w-2 h-2 rounded-full bg-[#C9A84C] shrink-0" title="Unsaved changes" />
              )}
            </button>

            {expanded && (
              <div className="px-5 pb-5 space-y-3 border-t border-[#1E2D4A]">
                {isError ? (
                  <div className="mt-4 space-y-3">
                    <p className="text-sm text-red-400">
                      This chapter failed to generate. Click below to retry.
                    </p>
                    {canRegenerate && (
                      <button
                        onClick={() => regenerateChapter(num)}
                        disabled={regenerating}
                        className="flex items-center gap-2 px-4 py-2 bg-[#1E2D4A] border border-red-900/50 text-red-400 rounded-md text-sm font-semibold hover:bg-red-900/20 transition-colors disabled:opacity-60"
                      >
                        <RefreshCw size={14} className={regenerating ? "animate-spin" : ""} />
                        {regenerating ? "Regenerating…" : "Regenerate Chapter"}
                      </button>
                    )}
                  </div>
                ) : (
                  <>
                    <textarea
                      className="w-full min-h-[200px] mt-4 bg-[#0F1729] border border-[#1E2D4A] rounded-md px-4 py-3 text-sm text-[#F5F3EE] leading-relaxed resize-y focus:outline-none focus:border-[#C9A84C]/50 transition-colors"
                      value={chapter.content}
                      onChange={(e) => updateChapterContent(num, e.target.value)}
                    />
                    {dirty && (
                      <div className="flex justify-end">
                        <button
                          onClick={() => saveChapter(chapter)}
                          disabled={saving}
                          className="flex items-center gap-2 px-4 py-2 bg-[#C9A84C] text-[#0F1729] rounded-md text-sm font-semibold hover:bg-[#B8963E] transition-colors disabled:opacity-60"
                        >
                          <Save size={14} />
                          {saving ? "Saving…" : "Save Chapter"}
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ── Quizzes ───────────────────────────────────────────────── */

interface QuizEditorProps {
  quizType: "chapter_review" | "final_assessment";
}

function QuizEditor({ quizType }: QuizEditorProps) {
  const [quizSets, setQuizSets] = useState<QuizSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dirtyQuizzes, setDirtyQuizzes] = useState<Set<string>>(new Set());
  const [savingQuiz, setSavingQuiz] = useState<string | null>(null);
  const [expandedQuizzes, setExpandedQuizzes] = useState<Set<string>>(new Set());

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .get<QuizSet[]>("/api/onboarding/quizzes")
      .then((data) => setQuizSets(data.filter((q) => q.quiz_type === quizType)))
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Failed to load quizzes");
      })
      .finally(() => setLoading(false));
  }, [quizType]);

  function toggleQuiz(id: string) {
    setExpandedQuizzes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function updateQuestion(
    quizId: string,
    questionIndex: number,
    field: keyof Question,
    value: string
  ) {
    setQuizSets((prev) =>
      prev.map((qs) =>
        qs.id !== quizId
          ? qs
          : {
              ...qs,
              questions: qs.questions.map((q, i) =>
                i === questionIndex ? { ...q, [field]: value } : q
              ),
            }
      )
    );
    setDirtyQuizzes((prev) => new Set(prev).add(quizId));
  }

  async function saveQuiz(quizSet: QuizSet) {
    setSavingQuiz(quizSet.id);
    try {
      await contentEditorApi.saveQuizSet(quizSet.id, quizSet.questions);
      setDirtyQuizzes((prev) => {
        const next = new Set(prev);
        next.delete(quizSet.id);
        return next;
      });
    } finally {
      setSavingQuiz(null);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (quizSets.length === 0)
    return (
      <EmptyState
        message={
          quizType === "final_assessment"
            ? "No final assessment generated yet."
            : "No quizzes generated yet."
        }
      />
    );

  return (
    <div className="space-y-3">
      {quizSets.map((qs, setIndex) => {
        const expanded = expandedQuizzes.has(qs.id);
        const dirty = dirtyQuizzes.has(qs.id);
        const saving = savingQuiz === qs.id;
        const label =
          quizType === "final_assessment"
            ? "Final Assessment"
            : `Quiz Set ${setIndex + 1}`;

        return (
          <div
            key={qs.id}
            className="bg-[#1A2540] border border-[#1E2D4A] rounded-lg overflow-hidden"
          >
            <button
              onClick={() => toggleQuiz(qs.id)}
              className="w-full flex items-center gap-3 px-5 py-4 text-left hover:bg-[#131E33] transition-colors"
            >
              {expanded ? (
                <ChevronDown size={16} className="text-[#64748B] shrink-0" />
              ) : (
                <ChevronRight size={16} className="text-[#64748B] shrink-0" />
              )}
              <span className="flex-1 text-sm text-[#F5F3EE] font-medium">
                {label}
              </span>
              <span className="text-xs text-[#64748B]">
                {qs.questions.length} question{qs.questions.length !== 1 ? "s" : ""}
              </span>
              {dirty && (
                <span className="w-2 h-2 rounded-full bg-[#C9A84C] ml-2 shrink-0" title="Unsaved changes" />
              )}
            </button>

            {expanded && (
              <div className="border-t border-[#1E2D4A] px-5 pb-5 space-y-5">
                {qs.questions.map((q, qi) => (
                  <QuestionFields
                    key={qi}
                    index={qi}
                    question={q}
                    onChange={(field, value) =>
                      updateQuestion(qs.id, qi, field, value)
                    }
                  />
                ))}

                {dirty && (
                  <div className="flex justify-end">
                    <button
                      onClick={() => saveQuiz(qs)}
                      disabled={saving}
                      className="flex items-center gap-2 px-4 py-2 bg-[#C9A84C] text-[#0F1729] rounded-md text-sm font-semibold hover:bg-[#B8963E] transition-colors disabled:opacity-60"
                    >
                      <Save size={14} />
                      {saving ? "Saving…" : "Save Quiz"}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

interface QuestionFieldsProps {
  index: number;
  question: Question;
  onChange: (field: keyof Question, value: string) => void;
}

function QuestionFields({ index, question, onChange }: QuestionFieldsProps) {
  return (
    <div className="mt-4 space-y-3">
      <p className="text-xs text-[#64748B] font-semibold uppercase tracking-wider">
        Q{index + 1}
      </p>
      <LabeledField label="Question">
        <textarea
          className={TEXTAREA_CLASS}
          value={question.text}
          rows={2}
          onChange={(e) => onChange("text", e.target.value)}
        />
      </LabeledField>
      <LabeledField label="Correct Answer">
        <input
          className={INPUT_CLASS}
          value={question.correct_answer}
          onChange={(e) => onChange("correct_answer", e.target.value)}
        />
      </LabeledField>
      <LabeledField label="Explanation">
        <textarea
          className={TEXTAREA_CLASS}
          value={question.explanation}
          rows={2}
          onChange={(e) => onChange("explanation", e.target.value)}
        />
      </LabeledField>
    </div>
  );
}

/* ── Checklist ─────────────────────────────────────────────── */

function ChecklistEditor() {
  const [checklist, setChecklist] = useState<ContractChecklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .get<ContractChecklist>("/api/onboarding/checklist")
      .then((data) => setChecklist(data))
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Failed to load checklist");
      })
      .finally(() => setLoading(false));
  }, []);

  const updateItem = useCallback(
    (
      catIndex: number,
      itemIndex: number,
      field: keyof ChecklistItem,
      value: string
    ) => {
      setChecklist((prev) => {
        if (!prev) return prev;
        const categories = prev.categories.map((cat, ci) => {
          if (ci !== catIndex) return cat;
          return {
            ...cat,
            items: cat.items.map((item, ii) =>
              ii !== itemIndex ? item : { ...item, [field]: value }
            ),
          };
        });
        return { ...prev, categories };
      });
      setDirty(true);
    },
    []
  );

  async function save() {
    if (!checklist) return;
    setSaving(true);
    try {
      await contentEditorApi.saveChecklist(checklist.categories);
      setDirty(false);
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!checklist) return <EmptyState message="No checklist generated yet." />;

  return (
    <div className="space-y-4">
      {checklist.categories.map((cat: ChecklistCategory, ci) => (
        <div
          key={ci}
          className="bg-[#1A2540] border border-[#1E2D4A] rounded-lg overflow-hidden"
        >
          <div className="px-5 py-3 border-b border-[#1E2D4A]">
            <span className="text-sm font-semibold text-[#C9A84C]">
              {cat.category}
            </span>
          </div>
          <div className="divide-y divide-[#1E2D4A]">
            {cat.items.map((item: ChecklistItem, ii) => (
              <div key={ii} className="px-5 py-4 space-y-2">
                <LabeledField label="Item">
                  <textarea
                    className={TEXTAREA_CLASS}
                    value={item.item}
                    rows={2}
                    onChange={(e) => updateItem(ci, ii, "item", e.target.value)}
                  />
                </LabeledField>
                <LabeledField label="Contract Value">
                  <input
                    className={INPUT_CLASS}
                    value={item.contract_value ?? ""}
                    onChange={(e) =>
                      updateItem(ci, ii, "contract_value", e.target.value)
                    }
                  />
                </LabeledField>
              </div>
            ))}
          </div>
        </div>
      ))}

      <div className="flex items-center justify-end gap-3 pt-2">
        {dirty && (
          <span className="flex items-center gap-1.5 text-xs text-[#C9A84C]">
            <span className="w-2 h-2 rounded-full bg-[#C9A84C]" />
            Unsaved changes
          </span>
        )}
        <button
          onClick={save}
          disabled={!dirty || saving}
          className="flex items-center gap-2 px-4 py-2 bg-[#C9A84C] text-[#0F1729] rounded-md text-sm font-semibold hover:bg-[#B8963E] transition-colors disabled:opacity-40"
        >
          <Save size={14} />
          {saving ? "Saving…" : "Save Checklist"}
        </button>
      </div>
    </div>
  );
}

/* ── Shared UI ─────────────────────────────────────────────── */

const TEXTAREA_CLASS =
  "w-full bg-[#0F1729] border border-[#1E2D4A] rounded-md px-3 py-2 text-sm text-[#F5F3EE] leading-relaxed resize-y focus:outline-none focus:border-[#C9A84C]/50 transition-colors";

const INPUT_CLASS =
  "w-full bg-[#0F1729] border border-[#1E2D4A] rounded-md px-3 py-2 text-sm text-[#F5F3EE] focus:outline-none focus:border-[#C9A84C]/50 transition-colors";

function LabeledField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1">
      <p className="text-xs text-[#64748B] font-medium">{label}</p>
      {children}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-14 bg-[#1A2540] rounded-lg border border-[#1E2D4A]" />
      ))}
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-[#1A2540] border border-red-900/50 rounded-lg px-5 py-4">
      <p className="text-sm text-red-400">{message}</p>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="bg-[#1A2540] border border-[#1E2D4A] rounded-lg px-5 py-8 text-center">
      <p className="text-sm text-[#64748B]">{message}</p>
    </div>
  );
}
