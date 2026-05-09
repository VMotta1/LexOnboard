"use client";

import { useState } from "react";
import type { ContractChecklist, ChecklistItem } from "@/types";

interface ChecklistToolProps {
  checklist: ContractChecklist;
}

export function ChecklistTool({ checklist }: ChecklistToolProps) {
  const allItems = checklist.categories.flatMap((cat) =>
    cat.items.map((item) => `${cat.category}::${item.item}`),
  );
  const [checked, setChecked] = useState<Set<string>>(new Set());
  const [confirmReset, setConfirmReset] = useState(false);

  function toggle(key: string) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function handlePrint() {
    window.print();
  }

  function handleReset() {
    if (!confirmReset) {
      setConfirmReset(true);
      return;
    }
    setChecked(new Set());
    setConfirmReset(false);
  }

  const total = allItems.length;
  const done = checked.size;

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
        <div className="flex items-center justify-between no-print">
          <p className="text-sm text-[#64748B]">
            <span className="text-[#F5F3EE] font-semibold">{done}</span> of{" "}
            <span className="text-[#F5F3EE] font-semibold">{total}</span> items checked
          </p>
          <div className="flex gap-2">
            <button
              onClick={handlePrint}
              className="text-xs px-3 py-1.5 border border-[#1E2D4A] rounded text-[#64748B] hover:border-[#C9A84C]/50 hover:text-[#F5F3EE] transition-colors"
            >
              Export Checklist (PDF)
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
              <button
                onClick={() => setConfirmReset(false)}
                className="text-xs text-[#64748B] hover:text-[#F5F3EE]"
              >
                Cancel
              </button>
            )}
          </div>
        </div>

        <div className="border border-[#1E2D4A] rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#1A2540] text-[#64748B] text-xs uppercase tracking-wider">
                <th className="w-8 px-3 py-3" />
                <th className="px-4 py-3 text-left">Category</th>
                <th className="px-4 py-3 text-left">Item / Clause</th>
                <th className="px-4 py-3 text-left">Review Question</th>
              </tr>
            </thead>
            <tbody>
              {checklist.categories.map((cat) => (
                <>
                  {cat.items.map((item: ChecklistItem, itemIdx: number) => {
                    const key = `${cat.category}::${item.item}`;
                    const isChecked = checked.has(key);
                    return (
                      <tr
                        key={key}
                        className={[
                          "border-t border-[#1E2D4A] transition-opacity",
                          item.is_mandatory ? "border-l-2 border-l-red-700" : "",
                          isChecked ? "opacity-60" : "",
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
                        <td className="px-4 py-3 text-[#8899BB]">
                          {itemIdx === 0 && (
                            <span className="flex items-center gap-1.5">
                              {item.is_mandatory && (
                                <span className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
                              )}
                              {cat.category}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-[#F5F3EE]">{item.item}</td>
                        <td className="px-4 py-3 text-[#8899BB]">{item.why_it_matters}</td>
                      </tr>
                    );
                  })}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
