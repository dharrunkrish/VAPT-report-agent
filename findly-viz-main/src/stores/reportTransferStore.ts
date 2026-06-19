import type { Finding } from "@/store/findingsStore";

const STORAGE_KEY = "vapt-transfer-payload-v1";

type Listener = () => void;

export interface TransferPayload {
  target: string;
  finding: Finding;
}

let pendingTransfer: TransferPayload | null = null;
const listeners = new Set<Listener>();

function readStored(): TransferPayload | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as TransferPayload) : null;
  } catch {
    return null;
  }
}

function notify() {
  listeners.forEach((listener) => listener());
}

export function setTransferPayload(payload: TransferPayload) {
  pendingTransfer = payload;
  if (typeof window !== "undefined") {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  }
  notify();
}

export function consumeTransferPayload(): TransferPayload | null {
  const payload = pendingTransfer ?? readStored();
  pendingTransfer = null;
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(STORAGE_KEY);
  }
  notify();
  return payload;
}

export function peekTransferPayload(): TransferPayload | null {
  return pendingTransfer ?? readStored();
}

export function subscribeTransferStore(listener: Listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
