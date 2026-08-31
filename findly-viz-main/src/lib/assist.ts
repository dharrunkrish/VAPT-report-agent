export async function requestStructuredAssist(payload: { finding: any; mode?: string; field?: string }) {
  const res = await fetch("/api/assist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || `Assist request failed (${res.status})`);
  }

  return await res.json();
}
