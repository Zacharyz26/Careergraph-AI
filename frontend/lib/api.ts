import type {
  AnalysisJobResponse,
  CandidateProfile,
  CareerDirectionResponse,
  JobProfile,
  MatchResult,
  PreferredLanguage,
  AnalysisHistoryResponse,
  ResumeUploadResponse,
  StoredAnalysisDetail,
  StoredSuggestionReview,
  SuggestionRequest,
  SuggestionReviewUpdateRequest,
  SuggestionResponse,
} from "@/lib/types";

const API_BASE_URL = resolveApiBaseUrl(
  process.env.NEXT_PUBLIC_API_BASE_URL,
).replace(/\/$/, "");
const API_V1_URL = API_BASE_URL.endsWith("/api/v1")
  ? API_BASE_URL
  : `${API_BASE_URL}/api/v1`;

function resolveApiBaseUrl(configuredBaseUrl?: string) {
  if (typeof window === "undefined") {
    return configuredBaseUrl || "http://127.0.0.1:8000";
  }

  const pageHostname = window.location.hostname;
  const configuredUrl = new URL(configuredBaseUrl || defaultApiBaseUrl());
  const isLocalConfiguredHost =
    configuredUrl.hostname === "localhost" ||
    configuredUrl.hostname === "127.0.0.1";
  const isLocalPageHost = pageHostname === "localhost" || pageHostname === "127.0.0.1";

  if (!isLocalPageHost && isLocalConfiguredHost) {
    configuredUrl.hostname = pageHostname;
  }

  return configuredUrl.toString();
}

function defaultApiBaseUrl() {
  if (typeof window === "undefined") return "http://127.0.0.1:8000";
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

export class APIError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function apiRequest<T>(path: string, init: RequestInit): Promise<T> {
  const url = `${API_V1_URL}${path}`;
  const headers = new Headers(init.headers);
  for (const [key, value] of Object.entries(workspaceHeaders())) {
    headers.set(key, value);
  }
  let response: Response;
  try {
    response = await fetch(url, { ...init, headers });
  } catch (error) {
    console.error("CareerGraph API request failed before receiving a response.", {
      url,
      error,
    });
    throw new APIError(
      `Could not reach the CareerGraph API at ${API_V1_URL}. Confirm the backend is running and this browser origin is allowed.`,
      0,
    );
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // Keep the status-based fallback when the server does not return JSON.
    }
    console.error("CareerGraph API request returned an error response.", {
      url,
      status: response.status,
      message,
    });
    throw new APIError(message, response.status);
  }

  return (await response.json()) as T;
}

function postJSON<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(body),
  });
}

export function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const body = new FormData();
  body.append("file", file);
  return apiRequest<ResumeUploadResponse>("/resumes/upload", {
    method: "POST",
    body,
  });
}

export function parseCandidateProfile(
  extractedText: string,
  preferredLanguage: PreferredLanguage = "en",
): Promise<CandidateProfile> {
  return postJSON<CandidateProfile>("/resumes/parse-profile", {
    extracted_text: extractedText,
    preferred_language: preferredLanguage,
  });
}

export function recommendCareerDirections(
  candidateProfile: CandidateProfile,
  preferredLanguage: PreferredLanguage = "en",
): Promise<CareerDirectionResponse> {
  return postJSON<CareerDirectionResponse>("/career-directions/recommend", {
    candidate_profile: candidateProfile,
    preferred_language: preferredLanguage,
  });
}

export function generateSuggestions(
  request: SuggestionRequest,
): Promise<SuggestionResponse> {
  return postJSON<SuggestionResponse>("/suggestions/generate", request);
}

export function parseJobDescription(
  rawJobDescription: string,
): Promise<JobProfile> {
  return postJSON<JobProfile>("/jobs/parse", {
    raw_job_description: rawJobDescription,
  });
}

export function scoreJobMatch(
  candidateProfile: CandidateProfile,
  jobProfile: JobProfile,
): Promise<MatchResult> {
  return postJSON<MatchResult>("/matches/score", {
    candidate_profile: candidateProfile,
    job_profile: jobProfile,
  });
}

export function createAnalysisJob(
  extractedText: string,
  preferredLanguage: PreferredLanguage = "en",
  resumeId?: string,
): Promise<AnalysisJobResponse> {
  return postJSON<AnalysisJobResponse>("/analysis-jobs", {
    extracted_text: extractedText,
    preferred_language: preferredLanguage,
    resume_id: resumeId,
  });
}

export function getAnalysisJob(jobId: string): Promise<AnalysisJobResponse> {
  return apiRequest<AnalysisJobResponse>(`/analysis-jobs/${jobId}`, {
    method: "GET",
  });
}

export function retryAnalysisJob(jobId: string): Promise<AnalysisJobResponse> {
  return postJSON<AnalysisJobResponse>(`/analysis-jobs/${jobId}/retry`, {});
}

export function listAnalysisHistory(): Promise<AnalysisHistoryResponse> {
  return apiRequest<AnalysisHistoryResponse>("/workspace/analyses", {
    method: "GET",
  });
}

export function getStoredAnalysis(
  analysisId: string,
): Promise<StoredAnalysisDetail> {
  return apiRequest<StoredAnalysisDetail>(`/workspace/analyses/${analysisId}`, {
    method: "GET",
  });
}

export function updateSuggestionReview(
  analysisId: string,
  reviewId: string,
  request: SuggestionReviewUpdateRequest,
): Promise<StoredSuggestionReview> {
  return apiRequest<StoredSuggestionReview>(
    `/workspace/analyses/${analysisId}/suggestions/${encodeURIComponent(reviewId)}`,
    {
      method: "PATCH",
      headers: jsonHeaders(),
      body: JSON.stringify(request),
    },
  );
}

function jsonHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    ...workspaceHeaders(),
  };
}

function workspaceHeaders(): HeadersInit {
  const email = process.env.NEXT_PUBLIC_WORKSPACE_USER_EMAIL;
  return email ? { "X-CareerGraph-User-Email": email } : {};
}
