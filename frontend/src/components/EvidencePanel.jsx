import React from 'react';
import { Eye, Bug, AlertTriangle } from 'lucide-react';

export default function EvidencePanel() {
  return (
    <div className="bg-[#0d1222] border border-slate-800/80 rounded-2xl p-5 shadow-xl">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-sm text-white flex items-center gap-2">
          <Eye size={16} className="text-blue-400" /> Captured Evidence
        </h3>
        <button className="text-[10px] text-blue-400 hover:underline uppercase font-bold tracking-wider cursor-pointer">VIEW ALL</button>
      </div>

      <div className="space-y-3">
        <div className="bg-[#131c31] border border-slate-800 rounded-xl p-3 flex items-center gap-3">
          <Bug size={22} className="text-red-400 shrink-0" />
          <div>
            <h4 className="text-xs font-semibold text-white">CTA Button Overlap</h4>
            <p className="text-[10px] text-slate-400 mt-0.5">Element `.btn-checkout` overlapped by notification banner.</p>
          </div>
        </div>

        <div className="bg-[#131c31] border border-slate-800 rounded-xl p-3 flex items-center gap-3">
          <AlertTriangle size={22} className="text-amber-400 shrink-0" />
          <div>
            <h4 className="text-xs font-semibold text-white">Low Contrast Ratio</h4>
            <p className="text-[10px] text-slate-400 mt-0.5">Footer nav text fails WCAG AA standard requirement.</p>
          </div>
        </div>
      </div>
    </div>
  );
}