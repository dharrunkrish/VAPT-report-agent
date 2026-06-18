import type { GenerateReportRequest } from "@/services/reportApi";

const STORAGE_KEY = "vapt-transfer-payload-v1";

type Listener = () => void;

let pendingTransfer: GenerateReportRequest | null = null;
const listeners = new Set<Listener>();

function readStored(): GenerateReportRequest | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as GenerateReportRequest) : null;
  } catch {
    return null;
  }
}

function notify() {
  listeners.forEach((listener) => listener());
}

export function setTransferPayload(payload: GenerateReportRequest) {
  pendingTransfer = payload;
  if (typeof window !== "undefined") {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  }
  notify();
}

export function consumeTransferPayload(): GenerateReportRequest | null {
  const payload = pendingTransfer ?? readStored();
  pendingTransfer = null;
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(STORAGE_KEY);
  }
  notify();
  return payload;
}

export function peekTransferPayload(): GenerateReportRequest | null {
  return pendingTransfer ?? readStored();
}

export function subscribeTransferStore(listener: Listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
