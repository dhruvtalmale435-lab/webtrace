import React, { useState } from 'react';
import { Bot, Play } from 'lucide-react';

export default function TestForm({ onStartTest, isRunning }) {
  const [url, setUrl] = useState('https://ecommerce-website.com');
  const [objective, setObjective] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onStartTest(url, objective);
  };

  return (
    <div className="bg-[#0D1222] border border-slate-800/80 rounded-2xl p-6 shadow-xl flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center gap-2 mb-4">
          <div className="p-1.5 bg-blue-500/10 rounded-lg text-blue-400">
            <Bot className="w-4 h-4" />
          </div>
          <h3 className="font-semibold text-sm">Start a New Test</h3>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-slate-400 mb-1.5 block">Website URL *</label>
            <input 
              type="text" 
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full bg-[#13192B] border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="https://example.com"
              required
            />
          </div>

          <div>
            <label className="text-xs text-slate-400 mb-1.5 block">Test Objective *</label>
            <textarea 
              rows={3}
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              className="w-full bg-[#13192B] border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 transition-colors resize-none"
              placeholder="e.g. Check whether a user can add a product to the cart and proceed to checkout."
              required
            />
          </div>

          <div className="pt-2 flex justify-between items-center border-t border-slate-800/50">
            <span className="text-xs text-slate-400 cursor-pointer hover:text-slate-200">Advanced Settings v</span>
            <button 
              type="submit"
              disabled={isRunning}
              className="bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs px-5 py-2.5 rounded-xl shadow-lg shadow-blue-600/25 flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {isRunning ? 'Running...' : 'Start Test'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}