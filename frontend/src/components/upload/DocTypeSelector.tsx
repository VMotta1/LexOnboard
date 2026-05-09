"use client";

interface DocTypeSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

const DOC_TYPES = [
  "Master Agreement",
  "Compliance Document",
  "NDA",
  "Statement of Work",
  "Other",
];

export function DocTypeSelector({ value, onChange }: DocTypeSelectorProps) {
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-[#8899BB]">
        Document Type <span className="text-red-400">*</span>
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-[#0D1829] border border-[#1E2D4A] text-[#F5F3EE] rounded-md px-3 py-2.5 text-sm focus:outline-none focus:border-[#C9A84C] transition-colors"
      >
        <option value="">Select document type…</option>
        {DOC_TYPES.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
    </div>
  );
}
