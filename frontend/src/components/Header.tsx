"use client";

import React from "react";
import { ShieldCheck, Zap, Activity } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-white">RecoverIQ</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                v0.1.0-alpha
              </span>
            </div>
            <p className="text-xs text-slate-400">AI Revenue Recovery for Razorpay</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-medium">
            <ShieldCheck className="h-3.5 w-3.5 text-amber-400" />
            <span>Razorpay Test Mode Active</span>
          </div>

          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs font-medium">
            <Activity className="h-3.5 w-3.5 text-emerald-400" />
            <span>Policy Engine: Guarded</span>
          </div>
        </div>
      </div>
    </header>
  );
}
