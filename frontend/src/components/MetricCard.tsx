"use client";

import React from "react";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  subtext?: string;
  icon: LucideIcon;
  trend?: {
    value: string;
    isPositive: boolean;
  };
  accentColor: "blue" | "emerald" | "amber" | "rose" | "purple";
}

const colorStyles = {
  blue: {
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "border-blue-500/20",
    glow: "group-hover:border-blue-500/40",
  },
  emerald: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/20",
    glow: "group-hover:border-emerald-500/40",
  },
  amber: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/20",
    glow: "group-hover:border-amber-500/40",
  },
  rose: {
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    border: "border-rose-500/20",
    glow: "group-hover:border-rose-500/40",
  },
  purple: {
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "border-purple-500/20",
    glow: "group-hover:border-purple-500/40",
  },
};

export function MetricCard({
  title,
  value,
  subtext,
  icon: Icon,
  trend,
  accentColor,
}: MetricCardProps) {
  const styles = colorStyles[accentColor];

  return (
    <div
      className={`group relative rounded-2xl bg-slate-800/60 p-6 border ${styles.border} ${styles.glow} backdrop-blur-sm transition-all duration-200 hover:shadow-xl hover:shadow-slate-950/50`}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-400">{title}</span>
        <div className={`p-2.5 rounded-xl ${styles.bg} ${styles.text}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline justify-between">
        <div className="text-3xl font-extrabold tracking-tight text-white">{value}</div>
        {trend && (
          <span
            className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-md ${
              trend.isPositive
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
            }`}
          >
            {trend.value}
          </span>
        )}
      </div>

      {subtext && <p className="mt-2 text-xs text-slate-400">{subtext}</p>}
    </div>
  );
}
