/**
 * S3-compatible object storage abstraction.
 * Implementations can target AWS S3, MinIO, Cloudflare R2, etc.
 */

import { mkdir, readFile, unlink, writeFile } from "node:fs/promises";
import path from "node:path";

export type StorageObject = {
  key: string;
  contentType: string;
  sizeBytes: number;
  etag?: string;
};

export type PutObjectInput = {
  key: string;
  body: Buffer | Uint8Array | string;
  contentType: string;
  metadata?: Record<string, string>;
};

export type SignedUrlOptions = {
  expiresInSeconds?: number;
};

export interface ObjectStorage {
  putObject(input: PutObjectInput): Promise<StorageObject>;
  getObject(key: string): Promise<Buffer>;
  deleteObject(key: string): Promise<void>;
  getSignedDownloadUrl(
    key: string,
    options?: SignedUrlOptions,
  ): Promise<string>;
  getSignedUploadUrl(
    key: string,
    contentType: string,
    options?: SignedUrlOptions,
  ): Promise<string>;
}

/**
 * In-memory storage for tests and ephemeral local use.
 */
export class MemoryObjectStorage implements ObjectStorage {
  private objects = new Map<string, { body: Buffer; contentType: string }>();

  async putObject(input: PutObjectInput): Promise<StorageObject> {
    const body =
      typeof input.body === "string"
        ? Buffer.from(input.body)
        : Buffer.from(input.body);
    this.objects.set(input.key, { body, contentType: input.contentType });
    return {
      key: input.key,
      contentType: input.contentType,
      sizeBytes: body.byteLength,
    };
  }

  async getObject(key: string): Promise<Buffer> {
    const found = this.objects.get(key);
    if (!found) throw new Error(`Object not found: ${key}`);
    return found.body;
  }

  async deleteObject(key: string): Promise<void> {
    this.objects.delete(key);
  }

  async getSignedDownloadUrl(
    key: string,
    options?: SignedUrlOptions,
  ): Promise<string> {
    const expires = options?.expiresInSeconds ?? 3600;
    return `/api/files/${encodeURIComponent(key)}?expires=${expires}`;
  }

  async getSignedUploadUrl(
    key: string,
    contentType: string,
    options?: SignedUrlOptions,
  ): Promise<string> {
    const expires = options?.expiresInSeconds ?? 3600;
    return `/api/files/upload/${encodeURIComponent(key)}?ct=${encodeURIComponent(contentType)}&expires=${expires}`;
  }
}

/**
 * Local filesystem-backed storage for development.
 */
export class LocalObjectStorage implements ObjectStorage {
  constructor(
    private readonly rootDir = path.join(process.cwd(), ".data", "storage"),
    private readonly baseUrl = "/api/files",
  ) {}

  private resolve(key: string): string {
    const safe = key.replace(/\.\./g, "").replace(/^\/+/, "");
    return path.join(this.rootDir, safe);
  }

  async putObject(input: PutObjectInput): Promise<StorageObject> {
    const body =
      typeof input.body === "string"
        ? Buffer.from(input.body)
        : Buffer.from(input.body);
    const filePath = this.resolve(input.key);
    await mkdir(path.dirname(filePath), { recursive: true });
    await writeFile(filePath, body);
    return {
      key: input.key,
      contentType: input.contentType,
      sizeBytes: body.byteLength,
    };
  }

  async getObject(key: string): Promise<Buffer> {
    return readFile(this.resolve(key));
  }

  async deleteObject(key: string): Promise<void> {
    try {
      await unlink(this.resolve(key));
    } catch {
      // ignore missing
    }
  }

  async getSignedDownloadUrl(
    key: string,
    options?: SignedUrlOptions,
  ): Promise<string> {
    const expires = options?.expiresInSeconds ?? 3600;
    return `${this.baseUrl}/${encodeURIComponent(key)}?expires=${expires}`;
  }

  async getSignedUploadUrl(
    key: string,
    contentType: string,
    options?: SignedUrlOptions,
  ): Promise<string> {
    const expires = options?.expiresInSeconds ?? 3600;
    return `${this.baseUrl}/upload/${encodeURIComponent(key)}?ct=${encodeURIComponent(contentType)}&expires=${expires}`;
  }
}

let memorySingleton: MemoryObjectStorage | null = null;

export function createObjectStorage(): ObjectStorage {
  if (process.env.NODE_ENV === "test") {
    if (!memorySingleton) memorySingleton = new MemoryObjectStorage();
    return memorySingleton;
  }
  // Future: if S3_ENDPOINT + S3_BUCKET are set, return S3ObjectStorage.
  // Credentials must come from env / vault — never commit secrets.
  return new LocalObjectStorage();
}
