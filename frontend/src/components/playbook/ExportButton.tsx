"use client";

import { useState } from "react";
import { Loader2, FileText, FileDown } from "lucide-react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";

type Format = "word" | "pdf";

interface ExportResponse {
  url: string;
}

async function doExport(format: Format): Promise<void> {
  const result = await api.post<ExportResponse>("/api/playbook/export", { format });
  window.open(result.url, "_blank");
}

function ExportBtn({ format, label, icon }: { format: Format; label: string; icon: React.ReactNode }) {
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    setLoading(true);
    try {
      await doExport(format);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Export failed";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="flex items-center gap-2 w-full px-3 py-2 text-sm border border-[#1E2D4A] rounded-md text-[#8899BB] hover:border-[#C9A84C]/50 hover:text-[#F5F3EE] transition-colors disabled:opacity-50"
    >
      {loading ? <Loader2 size={14} className="animate-spin" /> : icon}
      {label}
    </button>
  );
}

export function ExportButton() {
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider mb-2">Export</p>
      <ExportBtn format="word" label="Export as Word" icon={<FileText size={14} />} />
      <ExportBtn format="pdf" label="Export as PDF" icon={<FileDown size={14} />} />
    </div>
  );
}
