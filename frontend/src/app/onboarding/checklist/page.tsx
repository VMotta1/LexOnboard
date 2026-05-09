"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ContractChecklist } from "@/types";
import { ChecklistTool } from "@/components/onboarding/ChecklistTool";

function normalizeChecklist(raw: unknown): ContractChecklist {
  const data = raw as Record<string, unknown>;
  const id = (data.id as string) ?? "";
  const rawCats = (data.categories as unknown[]) ?? [];

  const categories = rawCats.flatMap((cat) => {
    const c = cat as Record<string, unknown>;

    // Flat shape: { category, items: [{ item, is_mandatory, risk_level, contract_value }] }
    if (Array.isArray(c.items) && c.items[0] && "item" in (c.items[0] as object)) {
      return [{ category: (c.category as string) || "Uncategorized", items: c.items as ContractChecklist["categories"][number]["items"] }];
    }

    // Nested shape: { name, subcategories: [{ name, items: [{ item_clause, ... }] }] }
    const catName = (c.name as string) ?? (c.category as string) ?? "";
    const subs = (c.subcategories as unknown[]) ?? [];

    if (subs.length > 0) {
      return subs.map((sub) => {
        const s = sub as Record<string, unknown>;
        const subName = (s.name as string) ?? "";
        const label = subName ? `${catName} — ${subName}` : catName;
        const items = ((s.items as unknown[]) ?? []).map((it) => {
          const i = it as Record<string, unknown>;
          return {
            item: (i.item_clause as string) ?? (i.item as string) ?? "",
            is_mandatory: Boolean(i.is_non_negotiable ?? i.is_mandatory ?? false),
            why_it_matters: (i.review_question as string) ?? (i.why_it_matters as string) ?? "",
          };
        });
        return { category: label, items };
      });
    }

    // Already flat with wrong field names: { name, items: [{ item_clause, ... }] }
    const items = ((c.items as unknown[]) ?? []).map((it) => {
      const i = it as Record<string, unknown>;
      return {
        item: (i.item_clause as string) ?? (i.item as string) ?? "",
        is_mandatory: Boolean(i.is_non_negotiable ?? i.is_mandatory ?? false),
        why_it_matters: (i.review_question as string) ?? (i.why_it_matters as string) ?? "",
      };
    });
    return [{ category: catName, items }];
  });

  return { id, categories };
}

export default function ChecklistPage() {
  const [checklist, setChecklist] = useState<ContractChecklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<unknown>("/api/onboarding/checklist")
      .then((raw) => setChecklist(normalizeChecklist(raw)))
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
