"use client";

import { useSyncExternalStore } from "react";

type Listener = () => void;

const listeners = new Set<Listener>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function subscribeBrowserStorage(listener: Listener) {
  listeners.add(listener);
  if (typeof window !== "undefined") {
    window.addEventListener("storage", listener);
  }
  return () => {
    listeners.delete(listener);
    if (typeof window !== "undefined") {
      window.removeEventListener("storage", listener);
    }
  };
}

export function notifyBrowserStorage() {
  emit();
}

export function useBrowserStorageValue<T>(
  read: () => T,
  serverValue: T,
): T {
  return useSyncExternalStore(
    subscribeBrowserStorage,
    read,
    () => serverValue,
  );
}
