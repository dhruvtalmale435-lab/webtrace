import React from 'react';

export default function LiveLogs() {
  const logs = [
    { time: '10:42:18', text: 'Request received. Initializing orchestrator...', tag: 'System' },
    { time: '10:42:20', text: 'Explorer Agent: Analyzing website structure...', tag: 'Explorer' },
    { time: '10:42:46', text: 'Tester Agent: Navigating to product page...', tag: 'Tester' },
    { time: '10:43:21', text: 'Tester Agent: Adding product to cart...', tag: 'Tester' },
    { time: '10:44:18', text: 'Visual Auditor: Checking visual issues...', tag: 'Auditor' },
    { time: '10:44:32', text: 'Detected overlapping text in cart summary', tag: 'Issue', err: true },
  ];

  return (
    <div className="bg-[#0D1222] border border-slate-800/80 rounded-2xl p-6 shadow-xl h-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-sm">Live Test Log</h3>
        <span className="text-[10px] bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/20">Live Stream</span>
      </div>

      <div className="space-y-2.5 font-mono text-[11px] max-h-56 overflow-y-auto pr-2">
        {logs.map((log, i) => (
          <div key={i} className="flex items-center justify-between text-slate-300 bg-[#13192B]/50 p-2 rounded-lg border border-slate-800/40">
            <span className="text-slate-500">{log.time}</span>
            <span className={`truncate mx-2 flex-1 ${log.err ? 'text-red-400 font-semibold' : ''}`}>{log.text}</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{log.tag}</span>
          </div>
        ))}
      </div>
    </div>
  );
}