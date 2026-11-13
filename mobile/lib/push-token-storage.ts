export function readStoredPushToken(): Promise<string | null> {
  return Promise.resolve(null);
}

export function writeStoredPushToken(_token: string): Promise<void> {
  return Promise.resolve();
}

export function deleteStoredPushToken(): Promise<void> {
  return Promise.resolve();
}
