"use client";

import { useState, useMemo } from "react";
import type { ContractChecklist, ChecklistItem } from "@/types";

const CATEGORY_ORDER = ["Compliance", "Key Clause Checklist", "Risk Flags"] as const;
type Category = typeof CATEGORY_ORDER[number] | "All";

const CATEGORY_STYLES: Record<typeof CATEGORY_ORDER[number], { pill: string; border: string }> = {
  "Compliance":          { pill: "bg-blue-900/30 text-blue-300 border border-blue-700/50",   border: "border-l-blue-500" },
  "Key Clause Checklist":{ pill: "bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/30", border: "border-l-[#C9A84C]" },
  "Risk Flags":          { pill: "bg-orange-900/30 text-orange-300 border border-orange-700/50", border: "border-l-orange-500" },
};

function canonicalCategory(raw: string | undefined): typeof CATEGORY_ORDER[number] {
  const s = (raw ?? "").toLowerCase();
  if (s.includes("compliance") || s.includes("privacy") || s.includes("gdpr")) return "Compliance";
  if (s.includes("risk") || s.includes("flag") || s.includes("red")) return "Risk Flags";
  return "Key Clause Checklist";
}

interface ChecklistToolProps {
  checklist: ContractChecklist;
}

export function ChecklistTool({ checklist }: ChecklistToolProps) {
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [confirmReset, setConfirmReset] = useState(false);
  const [activeFilter, setActiveFilter] = useState<Category>("All");

  const categories = useMemo(() => {
    const buckets: Record<typeof CATEGORY_ORDER[number], ChecklistItem[]> = {
      "Compliance": [],
      "Key Clause Checklist": [],
      "Risk Flags": [],
    };
    for (const cat of checklist.categories) {
      for (const item of cat.items) {
        const itemCat = (item as ChecklistItem & { category?: string }).category;
        const key = canonicalCategory(itemCat ?? cat.category);
        buckets[key].push(item);
      }
    }
    return CATEGORY_ORDER
      .map((name) => ({ category: name, items: buckets[name] }))
      .filter((c) => c.items.length > 0);
  }, [checklist.categories]);

  const visibleCategories = useMemo(() =>
    activeFilter === "All" ? categories : categories.filter((c) => c.category === activeFilter),
    [categories, activeFilter],
  );

  const allItems = categories.flatMap((cat) => cat.items.map((item) => `${cat.category}::${item.item}`));
  const total = allItems.length;
  const done = checked.size;

  function toggle(key: string) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  }

  function handleReset() {
    if (!confirmReset) { setConfirmReset(true); return; }
    setChecked(new Set());
    setConfirmReset(false);
  }

  return (
    <>
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { background: white !important; color: black !important; }
          table { width: 100%; border-collapse: collapse; }
          th, td { border: 1px solid #ccc; padding: 6px 8px; font-size: 12px; }
        }
      `}</style>

      <div className="space-y-4">
        {/* Top bar */}
        <div className="flex items-center justify-between no-print">
          <p className="text-sm text-[#64748B]">
            <span className="text-[#F5F3EE] font-semibold">{done}</span> of{" "}
            <span className="text-[#F5F3EE] font-semibold">{total}</span> items checked
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => window.print()}
              className="text-xs px-3 py-1.5 border border-[#1E2D4A] rounded text-[#64748B] hover:border-[#C9A84C]/50 hover:text-[#F5F3EE] transition-colors"
            >
              Export (PDF)
            </button>
            <button
              onClick={handleReset}
              className={[
                "text-xs px-3 py-1.5 border rounded transition-colors",
                confirmReset
                  ? "border-red-600 text-red-400 hover:bg-red-900/20"
                  : "border-[#1E2D4A] text-[#64748B] hover:border-red-600/50",
              ].join(" ")}
            >
              {confirmReset ? "Confirm Reset" : "Reset"}
            </button>
            {confirmReset && (
              <button onClick={() => setConfirmReset(false)} className="text-xs text-[#64748B] hover:text-[#F5F3EE]">
                Cancel
              </button>
            )}
          </div>
        </div>

        {/* Category filter tabs */}
        <div className="flex gap-2 flex-wrap no-print">
          <button
            onClick={() => setActiveFilter("All")}
            className={[
              "text-xs px-3 py-1.5 rounded border transition-colors",
              activeFilter === "All"
                ? "border-[#F5F3EE]/30 text-[#F5F3EE] bg-[#1A2540]"
                : "border-[#1E2D4A] text-[#64748B] hover:text-[#F5F3EE]",
            ].join(" ")}
          >
            All
          </button>
          {categories.map(({ category }) => {
            const style = CATEGORY_STYLES[category];
            const active = activeFilter === category;
            return (
              <button
                key={category}
                onClick={() => setActiveFilter(active ? "All" : category)}
                className={[
                  "text-xs px-3 py-1.5 rounded transition-colors",
                  active ? style.pill : "border border-[#1E2D4A] text-[#64748B] hover:text-[#F5F3EE]",
                ].join(" ")}
              >
                {category}
              </button>
            );
          })}
        </div>

        {/* Table */}
        <div className="border border-[#1E2D4A] rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#1A2540] text-[#64748B] text-xs uppercase tracking-wider">
                <th className="w-8 px-3 py-3" />
                <th className="px-4 py-3 text-left">Category</th>
                <th className="px-4 py-3 text-left">Review Question</th>
                <th className="px-4 py-3 text-left">Contract Value</th>
              </tr>
            </thead>
            <tbody>
              {visibleCategories.map(({ category, items }) =>
                items.map((item: ChecklistItem) => {
                  const key = `${category}::${item.item}`;
                  const isChecked = checked.has(key);
                  const catStyle = CATEGORY_STYLES[category];
                  return (
                    <tr
                      key={key}
                      className={[
                        "border-t border-[#1E2D4A] border-l-2 transition-opacity",
                        catStyle.border,
                        isChecked ? "opacity-50" : "",
                      ].join(" ")}
                    >
                      <td className="px-3 py-3 text-center">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggle(key)}
                          className="w-4 h-4 rounded accent-[#C9A84C] cursor-pointer"
                        />
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={["text-xs px-2 py-0.5 rounded", catStyle.pill].join(" ")}>
                          {item.is_mandatory && <span className="mr-1">●</span>}
                          {category}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[#F5F3EE]">{item.item}</td>
                      <td className="px-4 py-3 text-[#8899BB] text-xs font-mono">
                        {(item.contract_value ?? item.why_it_matters ?? "—").replace(/^Not extracted\s*[-–]\s*/i, "")}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
