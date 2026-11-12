import type { TokenPair } from "./types";

let tokens: TokenPair | null = null;

export async function readStoredTokens(): Promise<TokenPair | null> {
  return tokens;
}

export async function writeStoredTokens(value: TokenPair): Promise<void> {
  tokens = value;
}

export async function clearStoredTokens(): Promise<void> {
  tokens = null;
}
