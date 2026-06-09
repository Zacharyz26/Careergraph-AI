export type ProcessingState =
  | "pending"
  | "processing"
  | "completed"
  | "failed";

export interface ResumeUploadResponse {
  resume_id: string;
  job_id: string;
  state: ProcessingState;
}

export interface CandidateProfile {
  headline?: string;
  target_roles: string[];
  skills: string[];
  strengths: string[];
  gaps: string[];
}

export interface MatchResult {
  id: string;
  resume_id: string;
  job_id: string;
  state: ProcessingState;
  final_score?: number;
  missing_requirements: string[];
}
