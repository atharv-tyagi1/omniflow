import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchApi, handleZodError } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { 
  apiKeyListResponseSchema,
  createApiKeyResponseSchema,
  rotateApiKeyResponseSchema,
  revokeApiKeyResponseSchema,
  CreateApiKeyRequest,
  RotateApiKeyRequest
} from "./schemas"

export function useApiKeys(workspaceId: string, params: { page?: number, limit?: number, status?: string } = {}) {
  return useQuery({
    queryKey: queryKeys.apiKeys.list(workspaceId, params),
    queryFn: async () => {
      const data = await fetchApi(`/api/v1/api-keys`, {
        params: { ...params },
        requiredCapability: "apiKeys",
      })
      try {
        return apiKeyListResponseSchema.parse(data)
      } catch (error) {
        handleZodError(error)
      }
    },
    enabled: !!workspaceId,
    retry: (failureCount, error) => {
      if ((error as any).code === "VALIDATION_ERROR" || (error as any).code === "CAPABILITY_DISABLED") return false
      return failureCount < 3
    }
  })
}

export function useCreateApiKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: CreateApiKeyRequest) => {
      const response = await fetchApi(`/api/v1/api-keys`, {
        method: "POST",
        body: JSON.stringify(data),
        requiredCapability: "apiKeys",
      })
      try {
        return createApiKeyResponseSchema.parse(response)
      } catch (error) {
        handleZodError(error)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys", "list"] })
    }
  })
}

export function useRotateApiKey(keyId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: RotateApiKeyRequest) => {
      const response = await fetchApi(`/api/v1/api-keys/${keyId}/rotate`, {
        method: "POST",
        body: JSON.stringify(data),
        requiredCapability: "apiKeys",
      })
      try {
        return rotateApiKeyResponseSchema.parse(response)
      } catch (error) {
        handleZodError(error)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys", "list"] })
    }
  })
}

export function useRevokeApiKey(keyId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const response = await fetchApi(`/api/v1/api-keys/${keyId}`, {
        method: "DELETE",
        requiredCapability: "apiKeys",
      })
      try {
        return revokeApiKeyResponseSchema.parse(response)
      } catch (error) {
        handleZodError(error)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apiKeys", "list"] })
    }
  })
}
