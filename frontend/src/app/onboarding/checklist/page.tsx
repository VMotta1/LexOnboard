"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ContractChecklist } from "@/types";
import { ChecklistTool } from "@/components/onboarding/ChecklistTool";

export default function ChecklistPage() {
  const [checklist, setChecklist] = useState<ContractChecklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<ContractChecklist>("/api/onboarding/checklist")
      .then(setChecklist)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load checklist"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE] mb-2">
          Contract Review Checklist
        </h1>
        <p className="text-[#64748B]">Use this checklist every time you review a new contract</p>
      </div>

      {loading && (
        <div className="space-y-2 animate-pulse">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-12 bg-[#1A2540] rounded" />
          ))}
        </div>
      )}

      {error && (
        <div className="text-center py-20 text-[#64748B]">
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="text-sm text-[#C9A84C] hover:underline mt-2">
            Retry
          </button>
        </div>
      )}

      {!loading && checklist && <ChecklistTool checklist={checklist} />}
    </div>
  );
}
