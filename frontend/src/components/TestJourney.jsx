
const steps = [
  "Explore Website",
  "Plan Test",
  "Execute Actions",
  "Check Visuals",
  "Generate Report",
];

export default function TestJourney({ currentStep = -1 }) {
  return (
    <section style={{
      background: "#10213b",
      color: "white",
      padding: "24px",
      borderRadius: "12px",
      marginTop: "20px"
    }}>
      <h2>Test Journey</h2>
      <p style={{ color: "#aabbd3" }}>
        Follow the progress of your website test.
      </p>

      {steps.map((step, index) => {
        const completed = index < currentStep;
        const active = index === currentStep;

        return (
          <div key={step} style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "12px",
            marginTop: "8px",
            borderRadius: "8px",
            background: active ? "#203d60" : "#172c49"
          }}>
            <span style={{
              width: "28px",
              height: "28px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: "50%",
              background: completed ? "#16a34a" :
                active ? "#2563eb" : "#34445c"
            }}>
              {completed ? "✓" : index + 1}
            </span>

            <span>{step}</span>

            <span style={{ marginLeft: "auto", color: "#aabbd3" }}>
              {completed ? "Completed" :
                active ? "In progress" : "Waiting"}
            </span>
          </div>
        );
      })}
    </section>
  );
}
