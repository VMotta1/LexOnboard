"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { OrgPlaybook, PlaybookSection } from "@/types";
import { PlaybookViewer, PlaybookSkeleton } from "@/components/playbook/PlaybookViewer";
import { ExportButton } from "@/components/playbook/ExportButton";

export default function PlaybookPage() {
  const [playbook, setPlaybook] = useState<OrgPlaybook | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string | null>(null);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;

    function fetchPlaybook() {
      api
        .get<OrgPlaybook>("/api/playbook/current")
        .then((data) => {
          setPlaybook(data);
          const sections = data.sections as PlaybookSection[];
          if (sections.length > 0 && !activeSection) setActiveSection(sections[0].clause_type);
          if (data.onboarding_ready && interval) {
            clearInterval(interval);
            interval = null;
          }
        })
        .catch((err) => {
          setError(err instanceof ApiError ? err.message : "Failed to load playbook");
          if (interval) { clearInterval(interval); interval = null; }
        })
        .finally(() => setLoading(false));
    }

    fetchPlaybook();
    interval = setInterval(fetchPlaybook, 5000);

    return () => { if (interval) clearInterval(interval); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const sections: PlaybookSection[] = (playbook?.sections as PlaybookSection[]) ?? [];

  return (
    <div className="flex gap-6 min-h-full">
      <aside className="w-[220px] shrink-0 space-y-1">
        <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-3">Sections</p>
        {loading ? (
          <div className="space-y-2 animate-pulse">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-7 bg-[#1A2540] rounded" />
            ))}
          </div>
        ) : (
          sections.map((s) => (
            <button
              key={s.clause_type}
              onClick={() => setActiveSection(s.clause_type)}
              className={[
                "w-full text-left text-sm px-3 py-2 rounded transition-colors capitalize",
                activeSection === s.clause_type
                  ? "border-l-2 border-[#C9A84C] pl-[10px] bg-[#1A2540] text-[#F5F3EE]"
                  : "text-[#64748B] hover:text-[#F5F3EE] hover:bg-[#131E33]",
              ].join(" ")}
            >
              {s.clause_type.replace(/_/g, " ")}
            </button>
          ))
        )}
      </aside>

      <div className="flex-1 min-w-0">
        {loading && <PlaybookSkeleton />}
        {error && (
          <div className="text-center py-20 text-[#64748B]">
            <p className="text-red-400">{error}</p>
          </div>
        )}
        {!loading && !error && !playbook && (
          <div className="text-center py-20 space-y-3">
            <p className="text-[#64748B]">No playbook found.</p>
            <p className="text-sm text-[#64748B]">Upload documents to generate a playbook.</p>
          </div>
        )}
        {!loading && playbook && <PlaybookViewer playbook={playbook} activeSection={activeSection} />}
      </div>

      <aside className="w-[180px] shrink-0 space-y-4">
        {playbook && (
          <>
            <div className="space-y-2">
              <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider">Version</p>
              <p className="text-lg font-[family-name:var(--font-playfair)] text-[#C9A84C]">v{playbook.version}</p>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider">Generated</p>
              <p className="text-sm text-[#8899BB]">
                {playbook.created_at && !isNaN(new Date(playbook.created_at).getTime())
                  ? new Date(playbook.created_at).toLocaleDateString()
                  : new Date().toLocaleDateString()}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider">Sections</p>
              <p className="text-sm text-[#8899BB]">{sections.length}</p>
            </div>
            <hr className="border-[#1E2D4A]" />
            <ExportButton />
          </>
        )}
      </aside>
    </div>
  );
}
