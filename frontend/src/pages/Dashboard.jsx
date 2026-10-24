import React, { useState } from 'react';

export default function Dashboard({ userName = "User" }) {
  const [url, setUrl] = useState('https://ecommerce-demo.webtrace.ai');
  const [objective, setObjective] = useState('Verify full checkout flow with discount coupon applied');
  const [isRunning, setIsRunning] = useState(false);
  const [activeLogFilter, setActiveLogFilter] = useState('all');

  // Dynamic Time-Based Greeting
  const getGreeting = () => {
    const hours = new Date().getHours();
    if (hours >= 5 && hours < 12) return 'Good morning';
    if (hours >= 12 && hours < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const handleStartTest = (e) => {
    e.preventDefault();
    setIsRunning(true);
    setTimeout(() => setIsRunning(false), 4500);
  };

  const logs = [
    { type: 'info', time: '10:42:15', text: 'Initializing browser engine (Chromium v118)...' },
    { type: 'info', time: '10:42:18', text: 'Target URL opened. Constructing visual accessibility tree.' },
    { type: 'bug', time: '10:42:25', text: '[Bug Detected] Overlapping text in navbar checkout CTA button.' },
    { type: 'warning', time: '10:42:31', text: '[Visual Flaw] Contrast ratio on footer links below WCAG standard (2.8:1).' },
    { type: 'info', time: '10:42:40', text: 'Form submission completed. Session token captured.' }
  ];

  const filteredLogs = logs.filter(log => {
    if (activeLogFilter === 'all') return true;
    return log.type === activeLogFilter;
  });

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', backgroundColor: '#090e1a', color: '#e8f0fc', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', overflow: 'hidden', boxSizing: 'border-box' }}>
      
      {/* Sidebar Navigation */}
      <aside style={{ width: '260px', backgroundColor: '#0d1222', borderRight: '1px solid #1a2639', padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', flexShrink: 0 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '30px' }}>
            <div style={{ backgroundColor: '#2563eb', padding: '8px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '18px', boxShadow: '0 4px 12px rgba(37,99,235,0.3)' }}>🤖</div>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 'bold', margin: 0, color: '#fff' }}>WebTrace</h2>
              <p style={{ fontSize: '10px', color: '#64748b', margin: '2px 0 0 0', letterSpacing: '0.5px', textTransform: 'uppercase' }}>AI QA ENGINEER</p>
            </div>
          </div>

          <div style={{ fontSize: '10px', fontWeight: 'bold', color: '#64748b', letterSpacing: '0.8px', marginBottom: '10px', textTransform: 'uppercase' }}>Core Platform</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <button style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%', padding: '10px 12px', backgroundColor: '#17233c', color: '#fff', border: '1px solid #2a3d5e', borderRadius: '8px', fontSize: '12px', fontWeight: '500', cursor: 'pointer', textAlign: 'left' }}>
              📊 Dashboard
            </button>
            <button style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%', padding: '10px 12px', backgroundColor: 'transparent', color: '#94a3b8', border: 'none', borderRadius: '8px', fontSize: '12px', fontWeight: '500', cursor: 'pointer', textAlign: 'left' }}>
              ⚡ Live Runs
            </button>
            <button style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%', padding: '10px 12px', backgroundColor: 'transparent', color: '#94a3b8', border: 'none', borderRadius: '8px', fontSize: '12px', fontWeight: '500', cursor: 'pointer', textAlign: 'left' }}>
              🕒 Test History
            </button>

            <div style={{ fontSize: '10px', fontWeight: 'bold', color: '#64748b', letterSpacing: '0.8px', marginTop: '24px', marginBottom: '10px', textTransform: 'uppercase' }}>Analysis</div>
            <button style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%', padding: '10px 12px', backgroundColor: 'transparent', color: '#94a3b8', border: 'none', borderRadius: '8px', fontSize: '12px', fontWeight: '500', cursor: 'pointer', textAlign: 'left' }}>
              📁 Visual Audits
            </button>
            <button style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%', padding: '10px 12px', backgroundColor: 'transparent', color: '#94a3b8', border: 'none', borderRadius: '8px', fontSize: '12px', fontWeight: '500', cursor: 'pointer', textAlign: 'left' }}>
              ⚙️ Settings
            </button>
          </div>
        </div>

        <div style={{ backgroundColor: '#131d32', border: '1px solid #1e314d', padding: '12px', borderRadius: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
            <span style={{ color: '#46cdb3', fontSize: '12px' }}>🛡️</span>
            <span style={{ fontSize: '11px', fontWeight: '600', color: '#e8f0fc' }}>Enterprise QA AI</span>
          </div>
          <p style={{ fontSize: '10px', color: '#94a3b8', margin: 0, lineHeight: '1.4' }}>Autonomous VLM + Playwright runner active.</p>
        </div>
      </aside>

      {/* Main Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
        
        {/* Top Header */}
        <header style={{ backgroundColor: '#0d1222', borderBottom: '1px solid #1a2639', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, zIndex: 10 }}>
          <div>
            <h1 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#fff' }}>WebTrace Autonomous Control Center</h1>
            <p style={{ fontSize: '11px', color: '#64748b', margin: '2px 0 0 0' }}>Active Engine: Chromium / Vision LLM Pipeline</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', backgroundColor: '#132238', border: '1px solid #1e3a5f', padding: '6px 14px', borderRadius: '20px', color: '#46cdb3', fontWeight: '500' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#46cdb3' }}></span> System Ready
            </span>
            <span style={{ fontSize: '12px', backgroundColor: '#17253d', color: '#cbd5e1', padding: '6px 14px', borderRadius: '20px', border: '1px solid #1e293b' }}>
              {userName}
            </span>
          </div>
        </header>

        {/* Dashboard Workspace */}
        <main style={{ padding: '24px', maxWidth: '1600px', margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
          
          <div style={{ marginBottom: '20px' }}>
            <span style={{ fontSize: '10px', fontWeight: 'bold', letterSpacing: '1px', color: '#3b82f6', textTransform: 'uppercase' }}>Autonomous Testing Suite</span>
            <h2 style={{ fontSize: '22px', fontWeight: 'bold', color: '#fff', margin: '4px 0 2px 0' }}>{getGreeting()}, {userName} 👋</h2>
            <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>Run end-to-end multi-agent web verification with automatic defect and visual regression logging.</p>
          </div>

          {/* Status Strip */}
          <div style={{ backgroundColor: '#0d1222', border: '1px solid #1a2639', padding: '12px 20px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px', marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: isRunning ? '#3b82f6' : '#10b981' }}></span>
              <span>Status: <strong style={{ color: '#fff' }}>{isRunning ? 'Execution in Progress...' : 'Idle & Ready'}</strong></span>
            </div>
            <div style={{ fontSize: '11px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>🕒 Last Execution: 2 mins ago</span>
            </div>
          </div>

          {/* 3-Column Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', marginBottom: '24px' }}>
            
            {/* Column 1: Test Input & Journey */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ backgroundColor: '#0d1222', border: '1px solid #1a2639', borderRadius: '16px', padding: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                  <div style={{ backgroundColor: 'rgba(59,130,246,0.1)', padding: '8px', borderRadius: '8px', border: '1px solid rgba(59,130,246,0.2)', color: '#3b82f6' }}>🤖</div>
                  <div>
                    <h3 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#fff' }}>Trigger Agent Suite</h3>
                    <p style={{ fontSize: '10px', color: '#64748b', margin: '2px 0 0 0' }}>Enter target application URL and objective.</p>
                  </div>
                </div>

                <form onSubmit={handleStartTest}>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '500', color: '#94a3b8', marginBottom: '6px' }}>Application Target URL</label>
                  <input 
                    type="url" 
                    value={url} 
                    onChange={(e) => setUrl(e.target.value)}
                    style={{ width: '100%', backgroundColor: '#131c31', border: '1px solid #1f304f', borderRadius: '8px', padding: '10px 12px', color: '#fff', fontSize: '12px', marginBottom: '14px', boxSizing: 'border-box', outline: 'none' }}
                    required 
                  />

                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '500', color: '#94a3b8', marginBottom: '6px' }}>Test Objective / Goal</label>
                  <textarea 
                    rows={3} 
                    value={objective} 
                    onChange={(e) => setObjective(e.target.value)}
                    style={{ width: '100%', backgroundColor: '#131c31', border: '1px solid #1f304f', borderRadius: '8px', padding: '10px 12px', color: '#fff', fontSize: '12px', marginBottom: '14px', boxSizing: 'border-box', resize: 'none', outline: 'none' }}
                    required 
                  />

                  <button 
                    type="submit" 
                    disabled={isRunning}
                    style={{ width: '100%', backgroundColor: '#2563eb', color: '#fff', border: 'none', padding: '12px', borderRadius: '8px', fontWeight: '600', fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', opacity: isRunning ? 0.7 : 1 }}
                  >
                    {isRunning ? '⏳ Executing Pipeline...' : '▶ Run Autonomous Test'}
                  </button>
                </form>
              </div>

              {/* User Journey Map */}
              <div style={{ backgroundColor: '#0d1222', border: '1px solid #1a2639', borderRadius: '16px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#fff' }}>User Journey Map</h3>
                  <span style={{ fontSize: '10px', backgroundColor: '#1e293b', color: '#94a3b8', padding: '2px 8px', borderRadius: '10px', border: '1px solid #334155' }}>5 Steps</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px' }}>
                  {['Navigate', 'Search', 'Add Cart', 'Checkout', 'Verify'].map((step, idx) => (
                    <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
                      <div style={{ width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 'bold', backgroundColor: idx < 4 ? '#2563eb' : '#1e293b', color: idx < 4 ? '#fff' : '#64748b', border: '1px solid #3b82f6' }}>
                        {idx + 1}
                      </div>
                      <span style={{ fontSize: '10px', color: '#94a3b8' }}>{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Column 2: Agents & Logs */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ backgroundColor: '#0d1222', border: '1px solid #1a2639', borderRadius: '16px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>⚡ Multi-Agent Engine</h3>
                  <span style={{ fontSize: '10px', color: '#10b981', backgroundColor: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)', padding: '2px 8px', borderRadius: '10px', fontWeight: '500' }}>Ready</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ backgroundColor: '#131c31', border: '1px solid #1a2942', padding: '12px', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <strong style={{ fontSize: '12px', color: '#fff' }}>🤖 Explorer Agent</strong>
                      <span style={{ fontSize: '10px', color: '#10b981' }}>100%</span>
                    </div>
                    <p style={{ fontSize: '10px', color: '#64748b', margin: '0 0 8px 0' }}>Mapping page layout & DOM tree</p>
                    <div style={{ width: '100%', height: '4px', backgroundColor: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: '100%', height: '100%', backgroundColor: '#10b981' }}></div>
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#131c31', border: '1px solid #1a2942', padding: '12px', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <strong style={{ fontSize: '12px', color: '#fff' }}>▶ Playwright Tester Agent</strong>
                      <span style={{ fontSize: '10px', color: '#3b82f6' }}>{isRunning ? '66%' : '100%'}</span>
                    </div>
                    <p style={{ fontSize: '10px', color: '#64748b', margin: '0 0 8px 0' }}>Executing mouse clicks & input actions</p>
                    <div style={{ width: '100%', height: '4px', backgroundColor: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: isRunning ? '66%' : '100%', height: '100%', backgroundColor: '#3b82f6', transition: 'width 0.5s' }}></div>
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#131c31', border: '1px solid #1a2942', padding: '12px', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <strong style={{ fontSize: '12px', color: '#fff' }}>👁️ Visual Auditor Agent</strong>
                      <span style={{ fontSize: '10px', color: '#3b82f6' }}>{isRunning ? '33%' : '80%'}</span>
                    </div>
                    <p style={{ fontSize: '10px', color: '#64748b', margin: '0 0 8px 0' }}>Analyzing UI alignment & pixel anomalies</p>
                    <div style={{ width: '100%', height: '4px', backgroundColor: '#1e293b', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: isRunning ? '33%' : '80%', height: '100%', backgroundColor: '#3b82f6', transition: 'width 0.5s' }}></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Live Stream Logs */}
              <div style={{ backgroundColor: '#0d1222', border: '1px solid #1a2639', borderRadius: '16px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#fff' }}>📄 Live Stream Logs</h3>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {['all', 'bug', 'warning'].map(type => (
                      <button 
                        key={type}
                        onClick={() => setActiveLogFilter(type)}
                        style={{ fontSize: '10px', textTransform: 'capitalize', padding: '2px 8px', borderRadius: '4px', backgroundColor: activeLogFilter === type ? '#2563eb' : '#1e293b', color: activeLogFilter === type ? '#fff' : '#94a3b8', border: 'none', cursor: 'pointer' }}
                      >
                        {type === 'warning' ? 'Visual' : type}
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ backgroundColor: '#131c31', border: '1px solid #1a2942', borderRadius: '10px', padding: '12px', maxHeight: '160px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {filteredLogs.map((log, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px' }}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: log.type === 'bug' ? '#ef4444' : log.type === 'warning' ? '#f59e0b' : '#10b981' }}></span>
                      <span style={{ color: '#64748b', fontFamily: 'monospace', fontSize: '10px' }}>{log.time}</span>
                      <span style={{ color: log.type === 'bug' ? '#fca5a5' : log.type === 'warning' ? '#fde68a' : '#cbd5e1' }}>{log.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Column 3: Metrics & Evidence */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ backgroundColor: '#0d1222', border: '1px solid #1a2639', borderRadius: '16px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#fff' }}>Execution Summary</h3>
                  <span style={{ fontSize: '10px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.2)', padding: '2px 8px', borderRadius: '10px', fontWeight: '600' }}>92% Health</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
                  <div style={{ backgroundColor: '#131c31', border: '1px solid #1a2942', padding: '12px', borderRadius: '10px', textAlign: 'center' }}>
                    <span style={{ fontSize: '14px' }}>✅</span>
                    <span style={{ fontSize: '10px', color: '#64748b', display: 'block', margin: '4px 0 2px 0' }}>Passed</span>
                    <strong style={{ fontSize: '14px', color: '#fff' }}>4 / 5</strong>
                  </div>
                  <div style={{ backgroundColor: '#131c31', border: '1px solid #1a2942', padding: '12px', borderRadius: '10px', textAlign: 'center' }}>
                    <span style={{ fontSize: '14px' }}>🐛</span>
                    <span style={{ fontSize: '10px', color: '#64748b', display: 'block', margin: '4px 0 2px 0' }}>Bugs</span>
                    <strong style={{ fontSize: '14px', color: '#ef4444' }}>1</strong>
                  </div>
                  <div style={{ backgroundColor: '#131c31', border: '1px solid #1a2942', padding: '12px', borderRadius: '10px', textAlign: 'center' }}>
                    <span style={{ fontSize: '14px' }}>⚠️</span>
                    <span style={{ fontSize: '10px', color: '#64748b', display: 'block', margin: '4px 0 2px 0' }}>Visual Flaws</span>
                    <strong style={{ fontSize: '14px', color: '#f59e0b' }}>1</strong>
                  </div>
                </div>
              </div>

              {/* Captured Evidence */}
              <div style={{ backgroundColor: '#0d1222', border: '1px solid #1a2639', borderRadius: '16px', padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>👁️ Captured Evidence</h3>
                  <button style={{ fontSize: '10px', color: '#3b82f6', background: 'none', border: 'none', fontWeight: 'bold', cursor: 'pointer', letterSpacing: '0.5px' }}>VIEW ALL</button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ backgroundColor: '#131c31', border: '1px solid #1a2942', borderRadius: '10px', padding: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '18px' }}>🐛</span>
                    <div>
                      <h4 style={{ fontSize: '12px', fontWeight: '600', margin: 0, color: '#fff' }}>CTA Button Overlap</h4>
                      <p style={{ fontSize: '10px', color: '#94a3b8', margin: '2px 0 0 0' }}>Element `.btn-checkout` overlapped by notification banner.</p>
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#131c31', border: '1px solid #1a2942', borderRadius: '10px', padding: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '18px' }}>⚠️</span>
                    <div>
                      <h4 style={{ fontSize: '12px', fontWeight: '600', margin: 0, color: '#fff' }}>Low Contrast Ratio</h4>
                      <p style={{ fontSize: '10px', color: '#94a3b8', margin: '2px 0 0 0' }}>Footer nav text fails WCAG AA standard requirement.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* Bottom Table: Recent Autonomous Runs */}
          <div style={{ backgroundColor: '#0d1222', border: '1px solid #1a2639', borderRadius: '16px', padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#fff' }}>Recent Autonomous Runs</h3>
              <span style={{ fontSize: '10px', backgroundColor: '#1e293b', color: '#94a3b8', padding: '2px 8px', borderRadius: '10px', border: '1px solid #334155' }}>4 Executions Today</span>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', textAlign: 'left', fontSize: '12px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1a2639', color: '#64748b', fontSize: '11px' }}>
                    <th style={{ paddingBottom: '10px', fontWeight: '500' }}>TARGET URL</th>
                    <th style={{ paddingBottom: '10px', fontWeight: '500' }}>OBJECTIVE</th>
                    <th style={{ paddingBottom: '10px', fontWeight: '500' }}>STATUS</th>
                    <th style={{ paddingBottom: '10px', fontWeight: '500' }}>BUGS</th>
                    <th style={{ paddingBottom: '10px', fontWeight: '500' }}>TIME</th>
                  </tr>
                </thead>
                <tbody style={{ color: '#cbd5e1' }}>
                  <tr style={{ borderBottom: '1px solid #131c31' }}>
                    <td style={{ padding: '12px 0', color: '#3b82f6', fontFamily: 'monospace' }}>https://ecommerce-demo.webtrace.ai</td>
                    <td style={{ padding: '12px 0' }}>Checkout flow test with coupon</td>
                    <td style={{ padding: '12px 0' }}><span style={{ fontSize: '10px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.2)', padding: '2px 8px', borderRadius: '10px', fontWeight: '600' }}>PASSED</span></td>
                    <td style={{ padding: '12px 0', color: '#ef4444', fontWeight: '500' }}>1 Bug</td>
                    <td style={{ padding: '12px 0', color: '#64748b' }}>10:42 PM</td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #131c31' }}>
                    <td style={{ padding: '12px 0', color: '#3b82f6', fontFamily: 'monospace' }}>https://app.webtrace.ai/login</td>
                    <td style={{ padding: '12px 0' }}>OAuth & SSO authentication validation</td>
                    <td style={{ padding: '12px 0' }}><span style={{ fontSize: '10px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.2)', padding: '2px 8px', borderRadius: '10px', fontWeight: '600' }}>PASSED</span></td>
                    <td style={{ padding: '12px 0', color: '#10b981', fontWeight: '500' }}>0 Bugs</td>
                    <td style={{ padding: '12px 0', color: '#64748b' }}>08:15 PM</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '12px 0', color: '#3b82f6', fontFamily: 'monospace' }}>https://app.webtrace.ai/settings</td>
                    <td style={{ padding: '12px 0' }}>Profile update and avatar upload test</td>
                    <td style={{ padding: '12px 0' }}><span style={{ fontSize: '10px', backgroundColor: 'rgba(16,185,129,0.1)', color: '#10b981', border: '1px solid rgba(16,185,129,0.2)', padding: '2px 8px', borderRadius: '10px', fontWeight: '600' }}>PASSED</span></td>
                    <td style={{ padding: '12px 0', color: '#10b981', fontWeight: '500' }}>0 Bugs</td>
                    <td style={{ padding: '12px 0', color: '#64748b' }}>05:30 PM</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}