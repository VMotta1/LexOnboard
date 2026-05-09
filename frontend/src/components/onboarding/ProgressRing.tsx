"use client";

interface ProgressRingProps {
  percentage: number;
  label: string;
  size?: number;
}

export function ProgressRing({ percentage, label, size = 96 }: ProgressRingProps) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#1E2D4A"
          strokeWidth={6}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#C9A84C"
          strokeWidth={6}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.5s ease" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center" style={{ marginTop: size / 2 - 16 }}>
        <span className="font-[family-name:var(--font-playfair)] text-xl font-semibold text-[#F5F3EE]">
          {Math.round(percentage)}%
        </span>
      </div>
      <span className="text-xs text-[#64748B]">{label}</span>
    </div>
  );
}

export function ProgressRingStacked({ percentage, label, size = 96 }: ProgressRingProps) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#1E2D4A" strokeWidth={6} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#C9A84C"
            strokeWidth={6}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 0.5s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-[family-name:var(--font-playfair)] text-lg font-semibold text-[#F5F3EE]">
            {Math.round(percentage)}%
          </span>
        </div>
      </div>
      <span className="text-xs text-[#64748B] text-center">{label}</span>
    </div>
  );
}
