"use client";

import { Check, Loader2 } from "lucide-react";

export type StageState = "completed" | "active" | "pending";

interface Stage {
  label: string;
  state: StageState;
}

interface StageIndicatorProps {
  stages: Stage[];
}

export function StageIndicator({ stages }: StageIndicatorProps) {
  return (
    <div className="flex items-center gap-0">
      {stages.map((stage, i) => (
        <div key={stage.label} className="flex items-center">
          <div className="flex flex-col items-center gap-1.5">
            <div
              className={[
                "w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors",
                stage.state === "completed"
                  ? "border-[#C9A84C] bg-[#C9A84C]"
                  : stage.state === "active"
                    ? "border-[#C9A84C] bg-transparent"
                    : "border-[#1E2D4A] bg-transparent",
              ].join(" ")}
            >
              {stage.state === "completed" ? (
                <Check size={14} className="text-[#0F1729]" strokeWidth={3} />
              ) : stage.state === "active" ? (
                <Loader2 size={14} className="text-[#C9A84C] animate-spin" />
              ) : (
                <div className="w-2 h-2 rounded-full bg-[#1E2D4A]" />
              )}
            </div>
            <span
              className={[
                "text-xs whitespace-nowrap",
                stage.state === "completed" || stage.state === "active"
                  ? "text-[#C9A84C]"
                  : "text-[#64748B]",
              ].join(" ")}
            >
              {stage.label}
            </span>
          </div>

          {i < stages.length - 1 && (
            <div
              className={[
                "h-0.5 w-12 mx-1 mb-5 transition-colors",
                stage.state === "completed" ? "bg-[#C9A84C]" : "bg-[#1E2D4A]",
              ].join(" ")}
            />
          )}
        </div>
      ))}
    </div>
  );
}

export function progressToStages(progress: number, stage: string): Stage[] {
  const STAGES = ["Uploading", "Parsing", "NLP Analysis", "Distilling", "Ready"];

  const stageIndexMap: Record<string, number> = {
    ingesting: 1,
    nlp: 2,
    distilling: 3,
    complete: 4,
    error: 4,
  };

  const activeIndex = stageIndexMap[stage] ?? 0;

  return STAGES.map((label, i) => ({
    label,
    state:
      i < activeIndex
        ? "completed"
        : i === activeIndex
          ? "active"
          : "pending",
  }));
}
