"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { TextbookContent, OnboardingProgress } from "@/types";
import { TextbookReader } from "@/components/onboarding/TextbookReader";

export default function TextbookPage() {
  const [textbook, setTextbook] = useState<TextbookContent | null>(null);
  const [progress, setProgress] = useState<OnboardingProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<TextbookContent>("/api/onboarding/textbook"),
      api.get<OnboardingProgress>("/api/onboarding/progress"),
    ])
      .then(([tb, prog]) => {
        setTextbook(tb);
        setProgress(prog);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load textbook"))
      .finally(() => setLoading(false));
  }, []);

  async function handleChapterRead(chapterIndex: number) {
    try {
      const updated = await api.patch<OnboardingProgress>("/api/onboarding/progress", {
        chapters_read: [chapterIndex],
      });
      setProgress(updated);
    } catch {
      // best-effort
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[#1E2D4A] border-t-[#C9A84C] rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !textbook) {
    return (
      <div className="text-center py-20 space-y-3">
        <p className="text-[#64748B]">
          {error ?? "Content still being generated. Check back in a few minutes."}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="text-sm text-[#C9A84C] hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <TextbookReader
      textbook={textbook}
      chaptersRead={progress?.chapters_read ?? []}
      onChapterRead={handleChapterRead}
    />
  );
}
