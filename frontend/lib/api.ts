import type {
  CandidateProfile,
  CareerDirectionResponse,
  JobProfile,
  MatchResult,
  ResumeUploadResponse,
  SuggestionRequest,
  SuggestionResponse,
} from "@/lib/types";

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? defaultApiBaseUrl()
).replace(/\/$/, "");
const API_V1_URL = API_BASE_URL.endsWith("/api/v1")
  ? API_BASE_URL
  : `${API_BASE_URL}/api/v1`;

function defaultApiBaseUrl() {
  if (typeof window === "undefined") return "http://127.0.0.1:8000";
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
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
  const response = await fetch(`${API_V1_URL}${path}`, init);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // Keep the status-based fallback when the server does not return JSON.
    }
    throw new APIError(message, response.status);
  }

  return (await response.json()) as T;
}

function postJSON<T>(path: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
): Promise<CandidateProfile> {
  return postJSON<CandidateProfile>("/resumes/parse-profile", {
    extracted_text: extractedText,
  });
}

export function recommendCareerDirections(
  candidateProfile: CandidateProfile,
): Promise<CareerDirectionResponse> {
  return postJSON<CareerDirectionResponse>("/career-directions/recommend", {
    candidate_profile: candidateProfile,
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
