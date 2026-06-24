"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";

import {
  CareerDirectionCards,
  SelectedDirectionReport,
} from "@/components/career/CareerDirectionCards";
import { CandidateProfilePanel } from "@/components/resume/CandidateProfilePanel";
import { ResumeUploader } from "@/components/resume/ResumeUploader";
import { SuggestionPanel } from "@/components/suggestions/SuggestionPanel";
import { LoadingState } from "@/components/ui/LoadingState";
import { AnalysisHistoryPanel } from "@/components/workflow/AnalysisHistoryPanel";
import {
  formatCopy,
  languageNames,
  type PreferredLanguage,
  uiCopy,
} from "@/lib/i18n";
import {
  createAnalysisJob,
  generateSuggestions,
  APIError,
  getStoredAnalysis,
  getAnalysisJob,
  listAnalysisHistory,
  retryAnalysisJob,
  updateSuggestionReview,
  uploadResume,
} from "@/lib/api";
import type {
  AnalysisJobResponse,
  AnalysisStepKey,
  AnalysisStepStatus,
  CandidateProfile,
  CareerDirection,
  AnalysisHistoryItem,
  ResumeUploadResponse,
  StoredSuggestionReview,
  SuggestionReviewActionStatus,
  SuggestionResponse,
} from "@/lib/types";

export function CareerGraphWorkflow() {
  const replaceInputId = useId();
  const suggestionRequestIdRef = useRef(0);
  const [preferredLanguage, setPreferredLanguage] = useState<PreferredLanguage>("en");
  const [analysisJobId, setAnalysisJobId] = useState<string | null>(null);
  const [analysisJob, setAnalysisJob] = useState<AnalysisJobResponse | null>(null);
  const [upload, setUpload] = useState<ResumeUploadResponse | null>(null);
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [directions, setDirections] = useState<CareerDirection[]>([]);
  const [selectedDirection, setSelectedDirection] = useState<CareerDirection | null>(null);
  const [suggestions, setSuggestions] = useState<SuggestionResponse | null>(null);
  const [suggestionsLanguage, setSuggestionsLanguage] =
    useState<PreferredLanguage | null>(null);
  const [activeAnalysisId, setActiveAnalysisId] = useState<string | null>(null);
  const [suggestionReviews, setSuggestionReviews] = useState<StoredSuggestionReview[]>([]);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [directionsLoading, setDirectionsLoading] = useState(false);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [directionsError, setDirectionsError] = useState<string | null>(null);
  const [suggestionsError, setSuggestionsError] = useState<string | null>(null);

  const isAnalyzing =
    analysisJob?.status === "queued" || analysisJob?.status === "running";
  const t = uiCopy[preferredLanguage];
  const analysisStatus = isAnalyzing
    ? analysisStatusLabel(analysisJob, preferredLanguage)
    : directions.length
      ? t.statusDirectionsReady
      : profile
        ? t.statusProfileReady
        : upload
          ? t.statusResumePrepared
          : t.statusResumePrepared;

  const currentSuggestions =
    suggestionsLanguage === preferredLanguage ? suggestions : null;

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const result = await listAnalysisHistory();
      setAnalysisHistory(result.analyses);
    } catch {
      setAnalysisHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const refreshStoredReviewState = useCallback(async (analysisId: string) => {
    try {
      const detail = await getStoredAnalysis(analysisId);
      setSuggestionReviews(detail.analysis.suggestion_reviews);
    } catch {
      // The analysis result remains usable even if review metadata is delayed.
    }
  }, []);

  const applyAnalysisJob = useCallback(
    (job: AnalysisJobResponse) => {
      const profileStep = stepStatus(job, "profile_parsing");
      const directionsStep = stepStatus(job, "career_directions");
      const advisorStep = stepStatus(job, "advisor_suggestions");

      setAnalysisJob(job);
      setActiveAnalysisId(job.job_id);
      setProfileLoading(profileStep === "running");
      setDirectionsLoading(directionsStep === "running");
      setSuggestionsLoading(advisorStep === "running");
      setAnalysisError(
        job.status === "failed"
          ? (job.error_message ?? uiCopy[preferredLanguage].errorAnalysisUnavailable)
          : null,
      );

      if (job.profile) {
        setProfile(job.profile);
      }
      if (job.career_directions) {
        setDirections(job.career_directions.directions);
      }
      if (job.selected_direction) {
        setSelectedDirection(job.selected_direction);
      }
      const jobSuggestions = job.suggestions;
      if (jobSuggestions) {
        setSuggestions(jobSuggestions);
        setSuggestionsLanguage(job.preferred_language);
        setSuggestionReviews((current) =>
          current.length ? current : initialSuggestionReviews(jobSuggestions),
        );
      }
      if (job.status === "succeeded" || job.status === "failed") {
        void loadHistory();
        void refreshStoredReviewState(job.job_id);
      }
    },
    [loadHistory, preferredLanguage, refreshStoredReviewState],
  );

  useEffect(() => {
    let cancelled = false;
    async function refreshHistory() {
      setHistoryLoading(true);
      try {
        const result = await listAnalysisHistory();
        if (!cancelled) setAnalysisHistory(result.analyses);
      } catch {
        if (!cancelled) setAnalysisHistory([]);
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    }
    void refreshHistory();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!analysisJobId || !analysisJob) return;
    if (analysisJob.status === "succeeded" || analysisJob.status === "failed") return;
    const jobId = analysisJobId;

    let cancelled = false;
    async function pollJob() {
      try {
        const job = await getAnalysisJob(jobId);
        if (!cancelled) applyAnalysisJob(job);
      } catch (cause) {
        if (!cancelled) {
          setAnalysisError(messageFrom(cause, preferredLanguage));
        }
      }
    }

    const intervalId = window.setInterval(() => {
      void pollJob();
    }, 1600);
    void pollJob();

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [analysisJobId, analysisJob, applyAnalysisJob, preferredLanguage]);

  function handleLanguageChange(language: PreferredLanguage) {
    if (language === preferredLanguage) return;
    suggestionRequestIdRef.current += 1;
    setPreferredLanguage(language);
    setAnalysisJobId(null);
    setAnalysisJob(null);
    setActiveAnalysisId(null);
    setAnalysisError(null);
    setSuggestions(null);
    setSuggestionsLanguage(null);
    setSuggestionReviews([]);
    setSuggestionsError(null);
  }

  async function handleUpload(file: File) {
    suggestionRequestIdRef.current += 1;
    setAnalysisJobId(null);
    setAnalysisJob(null);
    setActiveAnalysisId(null);
    setAnalysisError(null);
    setUploadLoading(true);
    setProfileLoading(false);
    setDirectionsLoading(false);
    setUploadError(null);
    setUpload(null);
    setProfile(null);
    setDirections([]);
    setSelectedDirection(null);
    setSuggestions(null);
    setSuggestionsLanguage(null);
    setSuggestionReviews([]);
    setProfileError(null);
    setDirectionsError(null);
    setSuggestionsError(null);
    try {
      setUpload(await uploadResume(file));
    } catch (cause) {
      setUploadError(messageFrom(cause, preferredLanguage));
    } finally {
      setUploadLoading(false);
    }
  }

  async function handleAnalyzeResume() {
    if (!upload) return;
    suggestionRequestIdRef.current += 1;
    setAnalysisJobId(null);
    setAnalysisJob(null);
    setActiveAnalysisId(null);
    setAnalysisError(null);
    setProfileLoading(true);
    setDirectionsLoading(false);
    setSuggestionsLoading(false);
    setProfileError(null);
    setProfile(null);
    setDirections([]);
    setSelectedDirection(null);
    setSuggestions(null);
    setSuggestionsLanguage(null);
    setSuggestionReviews([]);
    setDirectionsError(null);
    setSuggestionsError(null);
    try {
      const job = await createAnalysisJob(
        upload.extracted_text,
        preferredLanguage,
        upload.resume_id,
      );
      setAnalysisJobId(job.job_id);
      applyAnalysisJob(job);
    } catch (cause) {
      setAnalysisError(messageFrom(cause, preferredLanguage));
    } finally {
      if (!analysisJobId) {
        setProfileLoading(false);
      }
    }
  }

  async function handleRetryAnalysis() {
    if (!analysisJobId) {
      await handleAnalyzeResume();
      return;
    }
    setAnalysisError(null);
    setProfileError(null);
    setDirectionsError(null);
    setSuggestionsError(null);
    setProfileLoading(true);
    try {
      const job = await retryAnalysisJob(analysisJobId);
      applyAnalysisJob(job);
    } catch (cause) {
      setAnalysisError(messageFrom(cause, preferredLanguage));
      setProfileLoading(false);
    }
  }

  async function handleSuggestions() {
    if (!profile || !selectedDirection) return;
    const requestLanguage = preferredLanguage;
    const requestId = suggestionRequestIdRef.current + 1;
    suggestionRequestIdRef.current = requestId;
    setSuggestionsLoading(true);
    setSuggestionsError(null);
    try {
      const result = await generateSuggestions({
        candidate_profile: profile,
        career_direction_result: selectedDirection,
        target_direction: selectedDirection.direction,
        suggestion_mode: "career_direction",
        preferred_language: requestLanguage,
      });
      if (suggestionRequestIdRef.current !== requestId) return;
      setSuggestions(result);
      setSuggestionsLanguage(requestLanguage);
      setSuggestionReviews(initialSuggestionReviews(result));
    } catch (cause) {
      if (suggestionRequestIdRef.current !== requestId) return;
      setSuggestionsError(messageFrom(cause, preferredLanguage));
    } finally {
      if (suggestionRequestIdRef.current === requestId) {
        setSuggestionsLoading(false);
      }
    }
  }

  async function handleOpenStoredAnalysis(analysisId: string) {
    try {
      const detail = await getStoredAnalysis(analysisId);
      const job = detail.analysis.analysis_job;
      suggestionRequestIdRef.current += 1;
      setPreferredLanguage(job.preferred_language);
      setAnalysisJobId(null);
      setActiveAnalysisId(detail.analysis.analysis_id);
      setAnalysisJob(job);
      setAnalysisError(null);
      setProfileError(null);
      setDirectionsError(null);
      setSuggestionsError(null);
      setProfileLoading(false);
      setDirectionsLoading(false);
      setSuggestionsLoading(false);
      if (detail.resume) {
        setUpload({
          resume_id: detail.resume.resume_id,
          filename: detail.resume.filename,
          file_type: detail.resume.file_type,
          extracted_text: detail.resume.extracted_text,
          character_count: detail.resume.character_count,
          page_count: detail.resume.page_count,
        });
      }
      setProfile(job.profile ?? null);
      setDirections(job.career_directions?.directions ?? []);
      setSelectedDirection(job.selected_direction ?? job.career_directions?.directions[0] ?? null);
      setSuggestions(job.suggestions ?? null);
      setSuggestionsLanguage(job.suggestions ? job.preferred_language : null);
      setSuggestionReviews(detail.analysis.suggestion_reviews);
    } catch (cause) {
      setAnalysisError(messageFrom(cause, preferredLanguage));
    }
  }

  async function handleSuggestionReview(
    reviewId: string,
    status: SuggestionReviewActionStatus,
    editedText?: string,
  ) {
    if (!activeAnalysisId) return;
    const updated = await updateSuggestionReview(activeAnalysisId, reviewId, {
      status,
      edited_text: editedText,
    });
    setSuggestionReviews((current) => {
      const next = current.filter((review) => review.review_id !== reviewId);
      return [...next, updated].sort((left, right) =>
        left.review_id.localeCompare(right.review_id),
      );
    });
    void loadHistory();
  }

  if (!upload) {
    return (
      <main className="career-console career-console--empty">
        <section className="landing-shell">
          <nav className="landing-nav" aria-label="CareerGraph overview">
            <a href="#upload">{t.landingPrimaryAction}</a>
            <a href="#how-it-works">{t.howItWorksTitle}</a>
            <a href="#history">{t.analysisHistoryTitle}</a>
            <LanguageSelector
              language={preferredLanguage}
              onChange={handleLanguageChange}
            />
          </nav>

          <section className="landing-hero">
            <div className="landing-hero__copy">
              <span className="landing-badge">{t.landingTrustBadge}</span>
              <h1>{t.landingHeadline}</h1>
              <p>{t.landingBody}</p>
              <div className="landing-proof-list">
                <span>{t.landingProofOne}</span>
                <span>{t.landingProofTwo}</span>
                <span>{t.landingProofThree}</span>
              </div>
              <div className="landing-actions">
                <a className="button button--dark" href="#upload">
                  {t.landingPrimaryAction}
                </a>
                <a className="button button--ghost" href="#history">
                  {t.landingSecondaryAction}
                </a>
              </div>
            </div>

            <div className="landing-upload-panel" id="upload">
              <ResumeUploader
                error={uploadError}
                isLoading={uploadLoading}
                language={preferredLanguage}
                onUpload={handleUpload}
                upload={upload}
              />
            </div>
          </section>

          <section className="landing-preview" aria-label={t.landingPreviewTitle}>
            <div>
              <span className="eyebrow">{t.appKicker}</span>
              <h2>{t.landingPreviewTitle}</h2>
              <p>{t.landingPreviewBody}</p>
            </div>
            <div className="preview-card-grid">
              <LandingPreviewCard
                body={t.previewDirectionsBody}
                icon="path"
                title={t.previewDirectionsTitle}
              />
              <LandingPreviewCard
                body={t.previewAuditBody}
                icon="audit"
                title={t.previewAuditTitle}
              />
              <LandingPreviewCard
                body={t.previewGapsBody}
                icon="gap"
                title={t.previewGapsTitle}
              />
              <LandingPreviewCard
                body={t.previewAdvisorBody}
                icon="advisor"
                title={t.previewAdvisorTitle}
              />
            </div>
          </section>

          <section className="landing-how" id="how-it-works">
            <div className="landing-section-heading">
              <span className="eyebrow">{t.landingNavAdvisor}</span>
              <h2>{t.howItWorksTitle}</h2>
              <p>{t.howItWorksBody}</p>
            </div>
            <div className="how-step-grid">
              <HowStep index="01" title={t.howStepOneTitle} body={t.howStepOneBody} />
              <HowStep index="02" title={t.howStepTwoTitle} body={t.howStepTwoBody} />
              <HowStep index="03" title={t.howStepThreeTitle} body={t.howStepThreeBody} />
            </div>
          </section>

          <section className="landing-history" id="history">
            <AnalysisHistoryPanel
              analyses={analysisHistory}
              isLoading={historyLoading}
              language={preferredLanguage}
              onOpen={handleOpenStoredAnalysis}
            />
          </section>
        </section>
      </main>
    );
  }

  if (!profile && !isAnalyzing && !profileError && !directionsError && !analysisError) {
    return (
      <main className="career-console career-console--ready">
        <header className="console-header">
          <div>
            <span className="hero-kicker">{t.brandKicker}</span>
            <h1>{t.uploadedTitle}</h1>
            <p>{uploadError ?? t.uploadedBody}</p>
          </div>
          <div className="console-header__actions">
            <div className="console-file-pill">
              <span className="file-type-icon">{upload.file_type.toUpperCase()}</span>
              <span>{upload.filename}</span>
              <label className="file-replace-button" htmlFor={replaceInputId}>
                {t.replace}
                <input
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  disabled={uploadLoading}
                  id={replaceInputId}
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) void handleUpload(file);
                    event.target.value = "";
                  }}
                  type="file"
                />
              </label>
            </div>
            <span className="console-status">{t.statusResumePrepared}</span>
            <LanguageSelector
              language={preferredLanguage}
              onChange={handleLanguageChange}
            />
          </div>
        </header>

        <section className="analysis-ready-panel">
          <div className="analysis-ready-panel__status">
            <span aria-hidden="true">✓</span>
            {t.readyBadge}
          </div>
          <h2>{t.readyTitle}</h2>
          <p>{t.readyBody}</p>
          <button
            className="button button--dark analysis-ready-panel__cta"
            disabled={uploadLoading}
            onClick={handleAnalyzeResume}
            type="button"
          >
            {t.analyzeResume}
          </button>
          <div className="analysis-output-grid" aria-label="Analysis outputs">
            <div>
              <strong>{t.evidenceProfile}</strong>
              <span>{t.evidenceProfileReady}</span>
            </div>
            <div>
              <strong>{t.careerDirections}</strong>
              <span>{t.careerDirectionsReady}</span>
            </div>
            <div>
              <strong>{t.advisorNextStep}</strong>
              <span>{t.advisorNextStepReady}</span>
            </div>
          </div>
        </section>

        <AnalysisHistoryPanel
          analyses={analysisHistory}
          isLoading={historyLoading}
          language={preferredLanguage}
          onOpen={handleOpenStoredAnalysis}
        />
      </main>
    );
  }

  return (
    <main className="career-console">
      <header className="console-header">
        <div>
          <span className="hero-kicker">{t.brandKicker}</span>
          <h1>{profile?.basic_info.full_name || t.workspaceTitle}</h1>
          <p>{uploadError ?? t.workspaceSubtitle}</p>
        </div>
        <div className="console-header__actions">
          <div className="console-file-pill">
            <span className="file-type-icon">{upload.file_type.toUpperCase()}</span>
            <span>{upload.filename}</span>
            <label className="file-replace-button" htmlFor={replaceInputId}>
              {t.replace}
              <input
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                disabled={uploadLoading || isAnalyzing}
                id={replaceInputId}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void handleUpload(file);
                  event.target.value = "";
                }}
                type="file"
              />
            </label>
          </div>
          <span className="console-status">{analysisStatus}</span>
          <button
            className="button button--dark"
            disabled={isAnalyzing || uploadLoading}
            onClick={handleAnalyzeResume}
            type="button"
          >
            {isAnalyzing ? t.analyzing : profile ? t.refreshAnalysis : t.analyzeResume}
          </button>
          <LanguageSelector
            language={preferredLanguage}
            onChange={handleLanguageChange}
          />
        </div>
      </header>

      <section className="console-workbench">
        <section className="console-main">
          {directions.length || directionsLoading || directionsError ? (
            <>
              {analysisJob && (isAnalyzing || analysisJob.status === "failed") ? (
                <AnalysisJobProgress
                  error={analysisError}
                  job={analysisJob}
                  language={preferredLanguage}
                  onRetry={handleRetryAnalysis}
                />
              ) : null}
              <CareerDirectionCards
                directions={directions}
                error={directionsError}
                isLoading={directionsLoading}
                language={preferredLanguage}
                onSelect={(direction) => {
                  suggestionRequestIdRef.current += 1;
                  setSelectedDirection(direction);
                  setSuggestions(null);
                  setSuggestionsLanguage(null);
                  setSuggestionReviews([]);
                  setSuggestionsError(null);
                }}
                selected={selectedDirection}
                showSelectedReport={false}
              />
            </>
          ) : (
            <section className="console-analysis-panel">
              <span className="eyebrow">{t.careerFit}</span>
              <h2>{isAnalyzing ? t.buildingBrief : t.readyToMap}</h2>
              <p>{t.analysisExplainer}</p>
              {analysisJob && (isAnalyzing || analysisJob.status === "failed") ? (
                <AnalysisJobProgress
                  error={analysisError}
                  job={analysisJob}
                  language={preferredLanguage}
                  onRetry={handleRetryAnalysis}
                />
              ) : isAnalyzing ? (
                <LoadingState compact label={t.loadingLabel} stages={[...t.loadingStages]} />
              ) : (
                <button
                  className="button button--primary"
                  onClick={handleAnalyzeResume}
                  type="button"
                >
                  {t.analyzeResume}
                </button>
              )}
              {profileError || directionsError || analysisError ? (
                <p className="upload-error" role="alert">{profileError ?? directionsError ?? analysisError}</p>
              ) : null}
            </section>
          )}
        </section>

        <aside className="console-inspector">
          {profile || profileLoading || profileError ? (
            <CandidateProfilePanel
              compact
              error={profileError}
              isLoading={profileLoading}
              language={preferredLanguage}
              profile={profile}
            />
          ) : (
            <section className="inspector-empty">
              <span className="eyebrow">{t.evidenceProfile}</span>
              <h2>{t.profileSummaryTitle}</h2>
              <p>{t.profileSummaryPending}</p>
            </section>
          )}

          <section className="advisor-cta-card">
            <span className="eyebrow">{t.advisorPlan}</span>
            <h2>{selectedDirection ? t.selectedGuidance : t.selectDirection}</h2>
            <p>
              {selectedDirection
                ? formatCopy(t.advisorForDirection, {
                    direction: selectedDirection.direction,
                  })
                : t.advisorPending}
            </p>
            {selectedDirection ? (
              <button
                className="button button--dark button--wide"
                disabled={suggestionsLoading}
                onClick={handleSuggestions}
                type="button"
              >
                {suggestionsLoading ? t.preparing : currentSuggestions ? t.refreshAdvisor : t.prepareAdvisor}
              </button>
            ) : null}
          </section>

          <section className="workspace-trust-note">
            <span className="eyebrow">{t.launchPrivacyTitle}</span>
            <p>{t.launchPrivacyBody}</p>
          </section>
        </aside>
      </section>

      {selectedDirection ? (
        <section className="console-report">
          <SelectedDirectionReport
            direction={selectedDirection}
            language={preferredLanguage}
          />
        </section>
      ) : null}

      <section className="console-secondary">
        {currentSuggestions || suggestionsLoading || suggestionsError ? (
            <SuggestionPanel
              error={suggestionsError}
              isLoading={suggestionsLoading}
              language={preferredLanguage}
              onReview={handleSuggestionReview}
              result={currentSuggestions}
              reviews={suggestionReviews}
            />
        ) : null}

      </section>
    </main>
  );
}

function AnalysisJobProgress({
  error,
  job,
  language,
  onRetry,
}: {
  error: string | null;
  job: AnalysisJobResponse;
  language: PreferredLanguage;
  onRetry: () => void;
}) {
  const t = uiCopy[language];
  return (
    <section className="analysis-job-progress" aria-live="polite">
      <div className="analysis-job-progress__header">
        <div>
          <span className="eyebrow">{t.statusAnalyzing}</span>
          <h3>{analysisStatusLabel(job, language)}</h3>
        </div>
        {job.status === "failed" ? (
          <button className="button button--primary" onClick={onRetry} type="button">
            {t.retryAnalysis}
          </button>
        ) : null}
      </div>
      <div className="analysis-step-list">
        {job.steps.map((step) => (
          <div
            className={`analysis-step analysis-step--${step.status}`}
            key={step.key}
          >
            <span className="analysis-step__marker" aria-hidden="true" />
            <div>
              <strong>{analysisStepLabel(step.key, language)}</strong>
              <span>{analysisStepStatusLabel(step.status, language)}</span>
              {step.message ? <p>{step.message}</p> : null}
            </div>
          </div>
        ))}
      </div>
      {error ? <p className="upload-error" role="alert">{error}</p> : null}
    </section>
  );
}

function LandingPreviewCard({
  body,
  icon,
  title,
}: {
  body: string;
  icon: "path" | "audit" | "gap" | "advisor";
  title: string;
}) {
  return (
    <article className="landing-preview-card">
      <span className={`landing-preview-icon landing-preview-icon--${icon}`} aria-hidden="true">
        <svg viewBox="0 0 24 24">
          {icon === "path" ? (
            <path d="M5 17c5-8 9-10 14-10M5 17h14M5 17l4-4" />
          ) : icon === "audit" ? (
            <path d="M6 7h12M6 12h8M6 17h5M17 14l2 2 4-5" />
          ) : icon === "gap" ? (
            <path d="M5 19l5-5 4 4 5-9M5 8h6M5 12h3" />
          ) : (
            <path d="M12 4v4M12 16v4M5 12h4M15 12h4M7.8 7.8l2.8 2.8M13.4 13.4l2.8 2.8M16.2 7.8l-2.8 2.8M10.6 13.4l-2.8 2.8" />
          )}
        </svg>
      </span>
      <h3>{title}</h3>
      <p>{body}</p>
    </article>
  );
}

function HowStep({
  body,
  index,
  title,
}: {
  body: string;
  index: string;
  title: string;
}) {
  return (
    <article className="how-step">
      <span>{index}</span>
      <h3>{title}</h3>
      <p>{body}</p>
    </article>
  );
}

function LanguageSelector({
  language,
  onChange,
}: {
  language: PreferredLanguage;
  onChange: (language: PreferredLanguage) => void;
}) {
  return (
    <div className="language-selector" aria-label="Language">
      {(Object.keys(languageNames) as PreferredLanguage[]).map((option) => (
        <button
          aria-pressed={language === option}
          className={language === option ? "language-option language-option--active" : "language-option"}
          key={option}
          onClick={() => onChange(option)}
          type="button"
        >
          {languageNames[option]}
        </button>
      ))}
    </div>
  );
}

function stepStatus(
  job: AnalysisJobResponse,
  step: AnalysisStepKey,
): AnalysisStepStatus | undefined {
  return job.steps.find((item) => item.key === step)?.status;
}

function initialSuggestionReviews(result: SuggestionResponse): StoredSuggestionReview[] {
  const now = new Date().toISOString();
  const sections = [
    ["resume_ready_improvements", result.resume_ready_improvements],
    ["positioning_advice", result.positioning_advice],
    ["evidence_gaps", result.evidence_gaps],
    ["recommended_next_actions", result.recommended_next_actions],
  ] as const;
  return sections.flatMap(([section, items]) =>
    items.map((item, index) => ({
      review_id: `${section}:${index}`,
      section,
      item_index: index,
      status: "pending_review" as const,
      original_text:
        "suggested_text" in item
          ? item.suggested_text
          : "advice" in item
            ? item.advice
            : "gap" in item
              ? item.gap
              : item.action,
      updated_at: now,
    })),
  );
}

function analysisStatusLabel(
  job: AnalysisJobResponse | null,
  language: PreferredLanguage,
) {
  const t = uiCopy[language];
  if (!job) return t.statusAnalyzing;
  if (job.status === "queued") return t.analysisQueued;
  if (job.status === "running") return t.analysisRunning;
  if (job.status === "failed") return t.analysisFailed;
  return t.analysisSucceeded;
}

function analysisStepLabel(step: AnalysisStepKey, language: PreferredLanguage) {
  const t = uiCopy[language];
  const labels: Record<AnalysisStepKey, string> = {
    profile_parsing: t.stepProfileParsing,
    career_directions: t.stepCareerDirections,
    advisor_suggestions: t.stepAdvisorSuggestions,
    job_matching: t.stepJobMatching,
  };
  return labels[step];
}

function analysisStepStatusLabel(
  status: AnalysisStepStatus,
  language: PreferredLanguage,
) {
  const t = uiCopy[language];
  const labels: Record<AnalysisStepStatus, string> = {
    pending: t.stepStatusPending,
    running: t.stepStatusRunning,
    succeeded: t.stepStatusSucceeded,
    failed: t.stepStatusFailed,
    skipped: t.stepStatusSkipped,
  };
  return labels[status];
}

function messageFrom(cause: unknown, language: PreferredLanguage): string {
  const t = uiCopy[language];
  if (cause instanceof APIError) {
    if (cause.status === 0) {
      return t.errorNetwork;
    }
    const normalized = cause.message.toLowerCase();
    if (
      normalized.includes("timed out") ||
      normalized.includes("timeout") ||
      normalized.includes("taking longer") ||
      normalized.includes("apitimeouterror")
    ) {
      return t.errorAnalysisTimeout;
    }
    if (
      cause.status >= 500 ||
      normalized.includes("openai") ||
      normalized.includes("llm") ||
      normalized.includes("api key") ||
      normalized.includes("openai_")
    ) {
      return t.errorAnalysisUnavailable;
    }
    return cause.message;
  }
  return cause instanceof Error ? cause.message : t.errorAnalysisUnavailable;
}
