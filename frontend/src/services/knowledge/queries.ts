import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchApi } from "@/lib/api-client"

export const knowledgeKeys = {
  all: ["knowledge"] as const,
  documents: () => [...knowledgeKeys.all, "documents"] as const,
  document: (id: string) => [...knowledgeKeys.documents(), id] as const,
  datasets: () => [...knowledgeKeys.all, "datasets"] as const,
}

export type Document = {
  id: string
  name: string
  status: string
  file_type: string
}

/**
 * Backend wraps every response in { success, data, message }.
 * These helpers unwrap the inner payload.
 */
type ApiWrapper<T> = { success: boolean; data: T; message: string }

export function useDocuments() {
  return useQuery({
    queryKey: knowledgeKeys.documents(),
    queryFn: async () => {
      // Returns { success, data: { documents: string[] }, message }
      const response = await fetchApi<ApiWrapper<{ documents: string[] }>>(
        `/api/v1/knowledge/documents`,
        { requiredCapability: "knowledgeDocuments" }
      )
      const docIds: string[] = response?.data?.documents ?? []

      // Fetch full details for each document id
      const docPromises = docIds.map(async (id) => {
        try {
          // Returns { success, data: { id, name, status, file_type }, message }
          const detail = await fetchApi<ApiWrapper<Document>>(
            `/api/v1/knowledge/documents/${id}`,
            { requiredCapability: "knowledgeDocuments" }
          )
          return detail?.data ?? null
        } catch {
          return null
        }
      })

      const docs = await Promise.all(docPromises)
      return docs.filter(Boolean) as Document[]
    },
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (uploadData: { name: string; file_type: string; file_url: string }) => {
      return fetchApi(`/api/v1/knowledge/documents`, {
        method: "POST",
        body: JSON.stringify(uploadData),
        requiredCapability: "knowledgeDocuments",
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.documents() })
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      return fetchApi(`/api/v1/knowledge/documents/${id}`, {
        method: "DELETE",
        requiredCapability: "knowledgeDocuments",
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.documents() })
    },
  })
}
