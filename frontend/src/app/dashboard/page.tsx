"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Upload } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { DocumentCard } from "@/components/upload/DocumentCard";
import type { DocumentListItem, OrgPlaybook } from "@/types";

const PAGE_SIZE = 10;

export default function DashboardPage() {
  const [allDocs, setAllDocs] = useState<DocumentListItem[]>([]);
  const [page, setPage] = useState(0);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [playbookVersion, setPlaybookVersion] = useState<number | null>(null);

  useEffect(() => {
    setLoadingDocs(true);
    api
      .get<DocumentListItem[]>("/api/documents/")
      .then((data) => setAllDocs(data))
      .catch(() => {})
      .finally(() => setLoadingDocs(false));
  }, []);

  useEffect(() => {
    api
      .get<OrgPlaybook>("/api/playbook/current")
      .then((pb) => setPlaybookVersion(pb.version))
      .catch(() => {});
  }, []);

  async function handleDelete(id: string) {
    try {
      await api.delete(`/api/documents/${id}`);
      setAllDocs((prev) => prev.filter((d) => d.id !== id));
      toast.success("Document deleted");
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Delete failed";
      toast.error(msg);
    }
  }

  const total = allDocs.length;
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const docs = allDocs.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  return (
    <div className="space-y-8 max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE]">
          Dashboard
        </h1>
        <Link
          href="/dashboard/upload"
          className="flex items-center gap-2 bg-[#C9A84C] text-[#0F1729] px-4 py-2 rounded-md text-sm font-semibold hover:bg-[#B8963E] transition-colors"
        >
          <Upload size={15} />
          Upload New Documents
        </Link>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <StatCard
          label="Documents Processed"
          value={total}
          loading={loadingDocs}
        />
        <StatCard
          label="Playbook Version"
          value={playbookVersion !== null ? `v${playbookVersion}` : "—"}
          loading={false}
        />
        <StatCard label="Team Members" value="—" loading={false} />
      </div>

      <section>
        <h2 className="font-[family-name:var(--font-playfair)] text-xl font-semibold text-[#F5F3EE] mb-4">
          Recent Documents
        </h2>

        {loadingDocs ? (
          <div className="space-y-2 animate-pulse">
            {[1, 2, 3].map((i) => <div key={i} className="h-14 bg-[#1A2540] rounded-md" />)}
          </div>
        ) : docs.length === 0 ? (
          <div className="border-2 border-dashed border-[#1E2D4A] rounded-lg py-20 text-center">
            <pre className="text-[#1E2D4A] text-xs mb-6 leading-tight select-none">
{`  ┌─────────────────────┐
  │                     │
  │   no documents yet  │
  │                     │
  └─────────────────────┘`}
            </pre>
            <p className="text-[#64748B] mb-6">
              No documents yet. Upload your first contract to get started.
            </p>
            <Link
              href="/dashboard/upload"
              className="inline-flex items-center gap-2 bg-[#C9A84C] text-[#0F1729] px-6 py-3 rounded-md font-semibold hover:bg-[#B8963E] transition-colors"
            >
              <Upload size={16} />
              Upload First Contract
            </Link>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              {docs.map((doc) => (
                <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4 text-sm text-[#64748B]">
                <span>
                  {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className="px-3 py-1.5 border border-[#1E2D4A] rounded disabled:opacity-40 hover:border-[#C9A84C]/50 transition-colors"
                  >
                    ← Prev
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                    disabled={page >= totalPages - 1}
                    className="px-3 py-1.5 border border-[#1E2D4A] rounded disabled:opacity-40 hover:border-[#C9A84C]/50 transition-colors"
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}

function StatCard({ label, value, loading }: { label: string; value: string | number; loading: boolean }) {
  return (
    <div className="bg-[#1A2540] border border-[#1E2D4A] rounded-lg px-5 py-4">
      <p className="text-xs text-[#64748B] uppercase tracking-wider mb-2">{label}</p>
      {loading ? (
        <div className="h-8 w-16 bg-[#0F1729] rounded animate-pulse" />
      ) : (
        <p className="font-[family-name:var(--font-playfair)] text-3xl font-semibold text-[#F5F3EE]">
          {value}
        </p>
      )}
    </div>
  );
}
