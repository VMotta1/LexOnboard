"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { PipelineStatus as PipelineStatusType } from "@/types";
import { StageIndicator, progressToStages } from "./StageIndicator";

interface PipelineStatusProps {
  jobId: string;
  documentId: string;
  onComplete: () => void;
}

export function PipelineStatus({ jobId, onComplete }: PipelineStatusProps) {
  const [status, setStatus] = useState<PipelineStatusType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const doneRef = useRef(false);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const data = await api.get<PipelineStatusType>(`/api/pipeline/status/${jobId}`);
        setStatus(data);

        if (data.stage === "complete" && !doneRef.current) {
          doneRef.current = true;
          clearInterval(interval);
          toast.success("Document processed — playbook updated");
          onComplete();
        } else if (data.stage === "error" && !doneRef.current) {
          doneRef.current = true;
          clearInterval(interval);
          setError(data.error ?? "Processing failed.");
        }
      } catch (err) {
        if (err instanceof Error) setError(err.message);
        clearInterval(interval);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [jobId, onComplete]);

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-sm text-red-300">
        <p className="font-medium mb-1">Processing failed</p>
        <p>{error}</p>
        <a href="mailto:support@lexonboard.com" className="underline text-red-400 mt-2 block">
          Contact support
        </a>
      </div>
    );
  }

  const stages = status ? progressToStages(status.progress_pct, status.stage) : progressToStages(0, "uploading");
  const pct = status?.progress_pct ?? 0;

  return (
    <div className="bg-[#0D1829] border border-[#1E2D4A] rounded-lg p-6 space-y-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-[#F5F3EE]">Processing document…</span>
        <span className="text-sm text-[#C9A84C] font-semibold">{pct}% complete</span>
      </div>
      <StageIndicator stages={stages} />
    </div>
  );
}
