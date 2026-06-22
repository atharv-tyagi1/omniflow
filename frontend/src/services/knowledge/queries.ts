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

export function useDocuments() {
  return useQuery({
    queryKey: knowledgeKeys.documents(),
    queryFn: async () => {
      const data = await fetchApi(`/api/v1/knowledge/documents`, {
        requiredCapability: "knowledgeDocuments",
      })
      // The API returns an array of IDs: { documents: ["uuid1", "uuid2"] }
      const docIds = data.documents as string[]
      
      // Fetch details for each document
      const docPromises = docIds.map(async (id) => {
        try {
          const detail = await fetchApi(`/api/v1/knowledge/documents/${id}`, {
            requiredCapability: "knowledgeDocuments",
          })
          return detail as Document
        } catch (e) {
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
