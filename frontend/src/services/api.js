const API_BASE_URL = "http://localhost:8000"; // FastAPI backend URL

export async function runTest(url, objective) {
  try {
    const response = await fetch(`${API_BASE_URL}/run-test`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url, objective }),
    });
    
    if (!response.ok) {
      throw new Error("Failed to start test execution");
    }
    
    return await response.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}