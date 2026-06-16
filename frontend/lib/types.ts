export type RoleFamily =
  | "Software Engineering"
  | "AI / Machine Learning"
  | "Data / Analytics"
  | "Product"
  | "Design"
  | "Marketing"
  | "Finance / Accounting"
  | "Business / Operations"
  | "Healthcare"
  | "Research"
  | "Education"
  | "Engineering"
  | "Sales / Customer Success"
  | "Human Resources"
  | "Legal / Compliance"
  | "General Internship"
  | "Other";

export type SeniorityLevel =
  | "Internship"
  | "Entry-level"
  | "Junior"
  | "Mid-level"
  | "Senior"
  | "Leadership"
  | "Unknown";

export interface ResumeUploadResponse {
  filename: string;
  file_type: "pdf" | "docx";
  extracted_text: string;
  character_count: number;
  page_count?: number;
}

export interface BasicInfo {
  full_name?: string;
  email?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  headline?: string;
}

export interface EducationItem {
  institution: string;
  degree?: string;
  field_of_study?: string;
  start_date?: string;
  graduation_date?: string;
  details: string[];
  evidence: string[];
}

export interface SkillGroup {
  category: string;
  skills: string[];
  evidence: string[];
}

export interface ExperienceItem {
  organization: string;
  title?: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  bullets: string[];
  evidence: string[];
}

export interface ProjectItem {
  name: string;
  description?: string;
  role?: string;
  technologies: string[];
  bullets: string[];
  url?: string;
  evidence: string[];
}

export interface InferredTargetRole {
  role: string;
  role_family: RoleFamily;
  seniority_level: SeniorityLevel;
  confidence: number;
  rationale: string;
  evidence: string[];
  is_inferred: true;
}

export interface CandidateProfile {
  basic_info: BasicInfo;
  education: EducationItem[];
  skills: SkillGroup[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  papers: Array<Record<string, unknown>>;
  patents: Array<Record<string, unknown>>;
  certifications: Array<{ name: string; issuer?: string; evidence: string[] }>;
  languages: Array<{ language: string; proficiency?: string; evidence: string[] }>;
  strengths: string[];
  improvement_areas: string[];
  inferred_target_roles: InferredTargetRole[];
}

export interface DirectionEvidence {
  evidence_id: string;
  source_type: string;
  text: string;
  evidence_strength: number;
  matched_concepts: string[];
}

export interface CareerDirection {
  rank: number;
  direction: string;
  role_family: RoleFamily;
  seniority_level: SeniorityLevel;
  fit_type: "primary" | "secondary" | "transferable" | "exploratory";
  score_range_low: number;
  score_range_high: number;
  score_midpoint: number;
  confidence_level: "High" | "Medium" | "Low";
  matched_evidence: DirectionEvidence[];
  strengths_for_this_direction: string[];
  gaps_for_this_direction: string[];
  resume_positioning_advice: string[];
  example_job_titles: string[];
}

export interface CareerDirectionResponse {
  directions: CareerDirection[];
}

export interface JobEvidenceItem {
  value: string;
  evidence: string[];
}

export interface JobProfile {
  job_title?: string;
  company_name?: string;
  role_family: RoleFamily;
  seniority_level: SeniorityLevel;
  employment_type: string;
  location?: string;
  remote_policy: string;
  salary?: Record<string, unknown>;
  visa_sponsorship?: string;
  required_skills: JobEvidenceItem[];
  preferred_skills: JobEvidenceItem[];
  responsibilities: JobEvidenceItem[];
  qualifications: JobEvidenceItem[];
  education_requirements: JobEvidenceItem[];
  experience_requirements: JobEvidenceItem[];
  benefits: JobEvidenceItem[];
  evidence: Record<string, string[]>;
}

export interface RequirementEvidence {
  source_type: string;
  text: string;
  evidence_strength: number;
  normalized_concepts: string[];
}

export interface RequirementMatch {
  requirement_type: string;
  importance: number;
  requirement: string;
  match_status:
    | "full_match"
    | "partial_match"
    | "transferable_match"
    | "missing";
  match_strength: number;
  confidence: number;
  similarity_score?: number;
  evaluation_method: string;
  candidate_evidence: RequirementEvidence[];
  reason: string;
}

export interface MatchResult {
  final_score: number;
  required_coverage_score: number;
  preferred_coverage_score: number;
  responsibility_alignment_score: number;
  education_fit_score: number;
  seniority_fit_score: number;
  evidence_strength_score: number;
  risk_penalty: number;
  requirement_matches: RequirementMatch[];
  matched_required_skills: string[];
  matched_preferred_skills: string[];
  missing_required_skills: string[];
  missing_preferred_skills: string[];
  transferable_matches: string[];
  matched_evidence: Array<Record<string, unknown>>;
  risks: string[];
  recommendation:
    | "Strong match"
    | "Good match after tailoring"
    | "Partial match"
    | "Low match";
  explanation: string;
}

export type SuggestionMode = "career_direction" | "job_specific" | "general";
export type AdvisorQuality = "high" | "medium" | "low";
export type EvidenceGapCategory =
  | "target_skill"
  | "tool_or_platform"
  | "implementation_or_delivery"
  | "portfolio_or_proof"
  | "impact_or_metrics"
  | "domain_experience"
  | "credential_or_education"
  | "communication_or_positioning"
  | "other";

export interface SuggestionItem {
  suggestion_type:
    | "bullet_rewrite"
    | "section_reorder"
    | "skill_grouping"
    | "project_emphasis"
    | "experience_emphasis"
    | "headline_summary"
    | "gap_disclosure"
    | "evidence_strengthening";
  target_section: string;
  original_text?: string;
  suggested_text: string;
  reason: string;
  source_evidence_ids: string[];
  source_evidence_text: string[];
  related_requirement_or_direction?: string;
  risk_level: "low" | "medium" | "high";
  quality_score: number;
  quality_level: AdvisorQuality;
  requires_user_review: true;
  should_add_to_resume: boolean;
}

export interface PositioningAdviceItem {
  target_section: string;
  advice: string;
  reason: string;
  source_evidence_ids: string[];
  source_evidence_text: string[];
  related_requirement_or_direction?: string;
  quality_score: number;
  quality_level: AdvisorQuality;
  requires_user_review: true;
}

export interface EvidenceGapItem {
  gap: string;
  category: EvidenceGapCategory;
  priority: "high" | "medium" | "low";
  why_it_matters: string;
  evidence_needed: string;
  related_requirement_or_direction?: string;
  should_add_to_resume: false;
  requires_user_review: true;
}

export interface RecommendedNextActionItem {
  action: string;
  rationale: string;
  target_gap?: string;
  suggested_artifact?: string;
  priority: "high" | "medium" | "low";
  quality_score: number;
  quality_level: AdvisorQuality;
  should_add_to_resume: false;
  requires_user_review: true;
}

export interface SuggestionResponse {
  overall_summary: string;
  resume_ready_improvements: SuggestionItem[];
  positioning_advice: PositioningAdviceItem[];
  evidence_gaps: EvidenceGapItem[];
  recommended_next_actions: RecommendedNextActionItem[];
  missing_but_not_addable: string[];
  warnings: string[];
}

export interface SuggestionRequest {
  candidate_profile: CandidateProfile;
  target_direction?: string;
  career_direction_result?: CareerDirection;
  job_profile?: JobProfile;
  match_result?: MatchResult;
  suggestion_mode: SuggestionMode;
}
