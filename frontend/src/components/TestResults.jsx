import React from 'react';

export default function TestResults() {
  return (
    <div className="bg-[#0D1222] border border-slate-800/80 rounded-2xl p-6 shadow-xl flex flex-col justify-between h-full">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-sm">Test Results</h3>
        <span className="text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">Passed</span>
      </div>

      <div className="flex items-center justify-center my-2">
        <div className="w-24 h-24 rounded-full border-4 border-emerald-500 border-t-red-500 flex items-center justify-center flex-col">
          <span className="text-xl font-bold">4/5</span>
          <span className="text-[10px] text-slate-400">Passed</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-[#13192B] p-2.5 rounded-xl border border-slate-800">
          <p className="text-slate-400 text-[10px]">Bugs Detected</p>
          <p className="text-lg font-bold text-red-400 mt-0.5">1 <span className="text-[10px] bg-red-500/20 px-1 rounded font-normal">High</span></p>
        </div>
        <div className="bg-[#13192B] p-2.5 rounded-xl border border-slate-800">
          <p className="text-slate-400 text-[10px]">Visual Issues</p>
          <p className="text-lg font-bold text-amber-400 mt-0.5">2 <span className="text-[10px] bg-amber-500/20 px-1 rounded font-normal">Medium</span></p>
        </div>
      </div>
    </div>
  );
}