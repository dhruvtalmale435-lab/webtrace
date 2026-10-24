import React from 'react';

export default function AgentProgress() {
  const agents = [
    { name: 'Explorer Agent', desc: 'Discovering relevant pages...', time: '00:48', progress: 100, done: true },
    { name: 'Tester Agent', desc: 'Executing browser actions...', time: '01:12', progress: 100, done: true },
    { name: 'Visual Auditor Agent', desc: 'Checking visual & layout issues...', time: '01:45', progress: 65, active: true },
    { name: 'Reporter Agent', desc: 'Compiling results and evidence...', time: 'Pending', progress: 0 }
  ];

  return (
    <div className="bg-[#0D1222] border border-slate-800/80 rounded-2xl p-6 shadow-xl space-y-4 h-full">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-sm">Multi-Agent Progress</h3>
        <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20">Running</span>
      </div>

      <div className="space-y-3.5">
        {agents.map((agent, i) => (
          <div key={i} className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-slate-300">{agent.name}</span>
              <span className="text-slate-500 text-[11px]">{agent.time}</span>
            </div>
            <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full ${agent.done ? 'bg-emerald-500' : agent.active ? 'bg-blue-500' : 'bg-slate-700'}`}
                style={{ width: `${agent.progress}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}