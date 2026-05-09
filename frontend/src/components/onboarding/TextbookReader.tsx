"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Check } from "lucide-react";
import { api } from "@/lib/api";
import type { TextbookContent, TextbookChapter } from "@/types";

function renderMarkdown(text: string): string {
  return text
    .replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold text-[#F5F3EE] mt-4 mb-2">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-lg font-semibold text-[#F5F3EE] mt-6 mb-2 font-[family-name:var(--font-playfair)]">$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-[#F5F3EE] font-semibold">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em class="text-[#8899BB]">$1</em>')
    .replace(/^- (.+)$/gm, '<li class="text-[#8899BB] ml-4 list-disc">$1</li>')
    .replace(/(<li[\s\S]*?<\/li>\n?)+/g, (m) => `<ul class="space-y-1 my-2">${m}</ul>`)
    .replace(/\n\n/g, '</p><p class="text-[#8899BB] leading-relaxed mb-4">')
    .replace(/^(?!<)(.+)$/gm, (m) => m ? `<p class="text-[#8899BB] leading-relaxed mb-4">${m}</p>` : "");
}

interface TextbookReaderProps {
  textbook: TextbookContent;
  chaptersRead: number[];
  onChapterRead: (index: number) => void;
}

export function TextbookReader({ textbook, chaptersRead, onChapterRead }: TextbookReaderProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const contentRef = useRef<HTMLDivElement>(null);
  const chapterRef = useRef<HTMLDivElement>(null);
  const [readProgress, setReadProgress] = useState(0);

  const chapter: TextbookChapter | undefined = textbook.chapters[activeIndex];

  const handleScroll = useCallback(() => {
    const el = chapterRef.current;
    if (!el) return;
    const { scrollTop, scrollHeight, clientHeight } = el;
    const pct = scrollHeight <= clientHeight ? 100 : (scrollTop / (scrollHeight - clientHeight)) * 100;
    setReadProgress(pct);
    if (pct >= 75 && chapter && !chaptersRead.includes(chapter.chapter_index)) {
      onChapterRead(chapter.chapter_index);
    }
  }, [chapter, chaptersRead, onChapterRead]);

  useEffect(() => {
    const el = chapterRef.current;
    if (!el) return;
    el.addEventListener("scroll", handleScroll);
    return () => el.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  useEffect(() => {
    chapterRef.current?.scrollTo({ top: 0 });
    setReadProgress(0);
  }, [activeIndex]);

  if (!chapter) return null;

  const totalChapters = textbook.chapters.length;

  return (
    <div className="flex gap-0 h-[calc(100vh-4rem)]">
      {/* Top reading progress bar */}
      <div className="fixed top-0 left-0 right-0 h-0.5 z-50 bg-[#1E2D4A]">
        <div
          className="h-full bg-[#C9A84C] transition-all duration-200"
          style={{ width: `${readProgress}%` }}
        />
      </div>

      {/* Chapter list sidebar */}
      <aside className="w-56 shrink-0 overflow-y-auto pr-4 space-y-1">
        <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-3">Chapters</p>
        {textbook.chapters.map((ch, i) => {
          const isRead = chaptersRead.includes(ch.chapter_index);
          const isActive = i === activeIndex;
          return (
            <button
              key={i}
              onClick={() => setActiveIndex(i)}
              className={[
                "w-full text-left flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors",
                isActive
                  ? "border-l-2 border-[#C9A84C] pl-[10px] bg-[#1A2540] text-[#F5F3EE]"
                  : "text-[#64748B] hover:text-[#F5F3EE] hover:bg-[#131E33]",
              ].join(" ")}
            >
              {isRead ? (
                <Check size={13} className="text-[#C9A84C] shrink-0" />
              ) : (
                <span className="w-[13px] h-[13px] rounded-full border border-[#1E2D4A] shrink-0" />
              )}
              <span className="truncate">{ch.title}</span>
            </button>
          );
        })}
      </aside>

      {/* Main reading area */}
      <div
        ref={chapterRef}
        className="flex-1 overflow-y-auto pl-8"
      >
        <div ref={contentRef} className="max-w-[720px] mx-auto pb-16">
          <p className="text-xs font-semibold text-[#C9A84C] uppercase tracking-widest mb-3">
            Chapter {activeIndex + 1}
          </p>
          <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE] mb-8">
            {chapter.title}
          </h1>

          <div
            className="prose-sm"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(chapter.content) }}
          />

          {chapter.key_takeaways.length > 0 && (
            <div className="mt-8 border border-[#C9A84C]/30 rounded-lg p-5 bg-[#C9A84C]/5">
              <p className="text-xs font-semibold text-[#C9A84C] uppercase tracking-wider mb-3">
                Key Takeaways
              </p>
              <ul className="space-y-2">
                {chapter.key_takeaways.map((t, i) => (
                  <li key={i} className="flex gap-2 text-sm text-[#F5F3EE]">
                    <span className="text-[#C9A84C] mt-0.5">•</span> {t}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex items-center justify-between mt-10 pt-6 border-t border-[#1E2D4A]">
            <button
              onClick={() => setActiveIndex((p) => Math.max(0, p - 1))}
              disabled={activeIndex === 0}
              className="text-sm text-[#64748B] hover:text-[#F5F3EE] disabled:opacity-30 transition-colors"
            >
              ← Previous Chapter
            </button>
            <span className="text-xs text-[#64748B]">
              {activeIndex + 1} / {totalChapters}
            </span>
            <button
              onClick={() => setActiveIndex((p) => Math.min(totalChapters - 1, p + 1))}
              disabled={activeIndex === totalChapters - 1}
              className="text-sm text-[#64748B] hover:text-[#F5F3EE] disabled:opacity-30 transition-colors"
            >
              Next Chapter →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
