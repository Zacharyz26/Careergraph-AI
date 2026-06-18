import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingState } from "@/components/ui/LoadingState";
import { type PreferredLanguage, uiCopy } from "@/lib/i18n";
import type { CandidateProfile } from "@/lib/types";

export function CandidateProfilePanel({
  profile,
  isLoading = false,
  error = null,
  compact = false,
  language = "en",
}: {
  profile: CandidateProfile | null;
  isLoading?: boolean;
  error?: string | null;
  compact?: boolean;
  language?: PreferredLanguage;
}) {
  const t = uiCopy[language];
  if (!profile) {
    if (compact && isLoading) {
      return (
        <section className="card result-card result-card--compact profile-loading-compact">
          <span className="eyebrow">{t.evidenceProfile}</span>
          <h2>{t.profileLoadingTitle}</h2>
          <p>{t.profileLoadingBody}</p>
          <div className="profile-skeleton" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </section>
      );
    }

    return (
      <section className={`card result-card${compact ? " result-card--compact" : ""}`}>
        <div className="card-heading">
          <div>
            <span className="eyebrow">{t.evidenceProfile}</span>
            <h2>{t.profileBuildingTitle}</h2>
            <p>{t.profileBuildingBody}</p>
          </div>
        </div>
        {error ? <ErrorMessage message={error} title={t.errorTitle} /> : null}
        {isLoading ? (
          <LoadingState
            detail={t.loadingDetail}
            label={t.profileLoadingLabel}
            stages={[...t.profileLoadingStages]}
          />
        ) : null}
      </section>
    );
  }

  const name = profile.basic_info.full_name || t.candidateProfile;
  const headline =
    profile.basic_info.headline ||
    profile.inferred_target_roles[0]?.role ||
    t.evidenceBasedProfile;

  return (
    <section className={`card result-card${compact ? " result-card--compact" : ""}`}>
      {error ? <ErrorMessage message={error} title={t.errorTitle} /> : null}
      {isLoading && compact ? (
        <div className="profile-inline-status" role="status">
          {t.profileRefreshing}
        </div>
      ) : isLoading ? (
        <LoadingState
          compact
          detail={t.profileRefreshDetail}
          label={t.profileRefreshLabel}
          stages={[...t.profileRefreshStages]}
        />
      ) : null}

      <div className="profile-header">
        <div className="avatar" aria-hidden="true">
          {name
            .split(" ")
            .slice(0, 2)
            .map((part) => part[0])
            .join("")
            .toUpperCase()}
        </div>
        <div>
          <span className="eyebrow">{t.evidenceProfile}</span>
          <h2>{name}</h2>
          <p>{headline}</p>
        </div>
      </div>

      <div className="profile-grid">
        <ProfileSection title={t.coreSkillSignals}>
          <div className="tag-list">
            {profile.skills.flatMap((group) =>
              group.skills.map((skill) => (
                <span className="tag" key={`${group.category}-${skill}`}>
                  {skill}
                </span>
              )),
            ).slice(0, compact ? 10 : undefined)}
          </div>
        </ProfileSection>

        <ProfileSection title={t.strongestProfileSignals}>
          {profile.strengths.length ? (
            <ul className="clean-list">
              {profile.strengths.slice(0, compact ? 3 : 4).map((strength) => (
                <li key={strength}>{strength}</li>
              ))}
            </ul>
          ) : (
            <p className="empty-copy">{t.noStrengths}</p>
          )}
        </ProfileSection>
      </div>

      <div className="profile-stats">
        <Stat value={profile.experience.length} label={t.experience} />
        <Stat value={profile.projects.length} label={t.projects} />
        <Stat value={profile.education.length} label={t.education} />
        <Stat value={profile.certifications.length} label={t.certifications} />
      </div>

      {compact ? null : (
        <details className="disclosure">
          <summary>{t.viewDetailedProfile}</summary>
          <pre>{JSON.stringify(profile, null, 2)}</pre>
        </details>
      )}
    </section>
  );
}

function ProfileSection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="profile-section">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}
