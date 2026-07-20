/**
 * S3-compatible object storage abstraction.
 * Implementations can target AWS S3, MinIO, Cloudflare R2, etc.
 */

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
 * Local filesystem-backed storage for development.
 * Replace with a real S3 client when S3_* env vars are configured.
 */
export class LocalObjectStorage implements ObjectStorage {
  constructor(private readonly baseUrl = "/api/files") {}

  async putObject(input: PutObjectInput): Promise<StorageObject> {
    // Placeholder — wire to disk or S3 in a later iteration.
    return {
      key: input.key,
      contentType: input.contentType,
      sizeBytes:
        typeof input.body === "string"
          ? Buffer.byteLength(input.body)
          : input.body.byteLength,
    };
  }

  async getObject(_key: string): Promise<Buffer> {
    throw new Error("LocalObjectStorage.getObject is not implemented yet");
  }

  async deleteObject(_key: string): Promise<void> {
    // no-op placeholder
  }

  async getSignedDownloadUrl(
    key: string,
    _options?: SignedUrlOptions,
  ): Promise<string> {
    return `${this.baseUrl}/${encodeURIComponent(key)}`;
  }

  async getSignedUploadUrl(
    key: string,
    _contentType: string,
    _options?: SignedUrlOptions,
  ): Promise<string> {
    return `${this.baseUrl}/upload/${encodeURIComponent(key)}`;
  }
}

export function createObjectStorage(): ObjectStorage {
  // Future: if S3_ENDPOINT + S3_BUCKET are set, return S3ObjectStorage.
  return new LocalObjectStorage();
}
