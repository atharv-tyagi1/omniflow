import { z } from "zod";

export const apiKeySchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  prefix: z.string(),
  status: z.enum(["active", "revoked"]),
  request_count: z.number(),
  rate_limit_tier: z.string(),
  last_used_at: z.string().nullable().optional(),
  created_at: z.string(),
});

export type ApiKey = z.infer<typeof apiKeySchema>;

export const apiKeyListResponseSchema = z.object({
  items: z.array(apiKeySchema),
  total: z.number(),
  page: z.number(),
  limit: z.number(),
});

export type ApiKeyListResponse = z.infer<typeof apiKeyListResponseSchema>;

export const createApiKeyRequestSchema = z.object({
  name: z.string().min(1, "Name is required").max(100, "Name too long"),
  scopes: z.array(z.string()).min(1, "At least one scope is required"),
});

export type CreateApiKeyRequest = z.infer<typeof createApiKeyRequestSchema>;

export const createApiKeyResponseSchema = z.object({
  key_secret: z.string(),
});

export type CreateApiKeyResponse = z.infer<typeof createApiKeyResponseSchema>;

export const rotateApiKeyRequestSchema = z.object({
  reason: z.string().optional(),
});

export type RotateApiKeyRequest = z.infer<typeof rotateApiKeyRequestSchema>;

export const rotateApiKeyResponseSchema = z.object({
  new_key_secret: z.string(),
});

export type RotateApiKeyResponse = z.infer<typeof rotateApiKeyResponseSchema>;

export const revokeApiKeyResponseSchema = z.object({
  success: z.boolean(),
});

export type RevokeApiKeyResponse = z.infer<typeof revokeApiKeyResponseSchema>;
