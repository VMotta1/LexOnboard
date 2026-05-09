"use client";

import { useState } from "react";
import { AlertTriangle, AlertOctagon, Info, ChevronDown, ChevronRight } from "lucide-react";
import type { OrgPlaybook, PlaybookSection, StandardPosition } from "@/types";

function ExpandablePosition({ position }: { position: StandardPosition }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-[#1E2D4A] rounded-md overflow-hidden">
      <button
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-[#1A2540] transition-colors"
      >
        <span className="text-sm font-medium text-[#F5F3EE]">{position.title}</span>
        {open ? (
          <ChevronDown size={15} className="text-[#64748B] shrink-0" />
        ) : (
          <ChevronRight size={15} className="text-[#64748B] shrink-0" />
        )}
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-[#1E2D4A] pt-3">
          <p className="text-sm text-[#F5F3EE]">{position.our_position}</p>
          {position.acceptable_variations.length > 0 && (
            <div>
              <p className="text-xs text-[#64748B] uppercase tracking-wider mb-1">Acceptable variations</p>
              <ul className="space-y-1">
                {position.acceptable_variations.map((v, i) => (
                  <li key={i} className="text-sm text-[#8899BB] flex gap-2">
                    <span className="text-[#64748B]">—</span> {v}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {position.rationale && (
            <p className="text-xs text-[#64748B] italic">{position.rationale}</p>
          )}
        </div>
      )}
    </div>
  );
}

function SectionBlock({ section }: { section: PlaybookSection }) {
  return (
    <div className="space-y-5">
      <h2 className="font-[family-name:var(--font-playfair)] text-xl font-semibold text-[#F5F3EE] capitalize">
        {section.clause_type.replace(/_/g, " ")}
      </h2>

      {section.non_negotiables.length > 0 && (
        <div className="border border-red-800/50 rounded-lg p-4 bg-red-900/10">
          <div className="flex items-center gap-2 mb-3">
            <AlertOctagon size={16} className="text-red-400" />
            <span className="text-xs font-semibold text-red-400 uppercase tracking-wider">Non-Negotiables</span>
          </div>
          <ul className="space-y-2">
            {section.non_negotiables.map((item, i) => (
              <li key={i} className="flex gap-2 text-sm text-[#F5F3EE]">
                <span className="text-red-500 mt-0.5">•</span> {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {section.standard_positions.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider">Standard Positions</p>
          {section.standard_positions.map((pos, i) => (
            <ExpandablePosition key={i} position={pos} />
          ))}
        </div>
      )}

      {section.red_flags.length > 0 && (
        <div className="border border-orange-700/50 rounded-lg p-4 bg-orange-900/10">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle size={16} className="text-orange-400" />
            <span className="text-xs font-semibold text-orange-400 uppercase tracking-wider">Red Flags</span>
          </div>
          <ul className="space-y-2">
            {section.red_flags.map((item, i) => (
              <li key={i} className="flex gap-2 text-sm text-[#F5F3EE]">
                <span className="text-orange-500 mt-0.5">•</span> {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {section.industry_baseline && (
        <div className="border border-[#1E2D4A] rounded-lg p-4 bg-[#0D1829]">
          <div className="flex items-center gap-2 mb-2">
            <Info size={14} className="text-[#64748B]" />
            <span className="text-xs font-semibold text-[#64748B] uppercase tracking-wider">Industry Baseline</span>
          </div>
          <p className="text-sm text-[#8899BB] italic">{section.industry_baseline}</p>
        </div>
      )}
    </div>
  );
}

export function PlaybookViewer({ playbook }: { playbook: OrgPlaybook }) {
  if (!playbook.onboarding_ready) {
    return (
      <div className="text-center py-20 text-[#64748B]">
        <div className="w-8 h-8 border-2 border-[#1E2D4A] border-t-[#C9A84C] rounded-full animate-spin mx-auto mb-4" />
        <p>Playbook generating…</p>
      </div>
    );
  }

  const sections: PlaybookSection[] = playbook.sections as PlaybookSection[];

  return (
    <div className="space-y-10">
      {sections.map((section, i) => (
        <div key={section.clause_type}>
          <SectionBlock section={section} />
          {i < sections.length - 1 && <hr className="mt-10 border-[#1E2D4A]" />}
        </div>
      ))}
    </div>
  );
}

export function PlaybookSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-3">
          <div className="h-6 bg-[#1A2540] rounded w-48" />
          <div className="h-24 bg-[#1A2540] rounded" />
          <div className="h-16 bg-[#1A2540] rounded" />
        </div>
      ))}
    </div>
  );
}
