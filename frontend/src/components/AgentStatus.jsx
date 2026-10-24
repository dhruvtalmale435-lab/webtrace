
function AgentStatus() {
  const agents = [
    { name: "Explorer Agent", status: "Waiting to explore website", progress: 0 },
    { name: "Tester Agent", status: "Waiting to execute tests", progress: 0 },
    { name: "Visual Auditor Agent", status: "Waiting to inspect layout", progress: 0 },
    { name: "Reporter Agent", status: "Waiting to generate report", progress: 0 }
  ];

  return (
    <section className="panel">
      <h2>Multi-Agent Progress</h2>

      {agents.map((agent) => (
        <div key={agent.name} className="agent-row">
          <div>
            <strong>{agent.name}</strong>
            <p>{agent.status}</p>
          </div>

          <div className="progress-track">
            <div
              className="progress-fill"
              style={{ width: `${agent.progress}%` }}
            />
          </div>
        </div>
      ))}
    </section>
  );
}

export default AgentStatus;
