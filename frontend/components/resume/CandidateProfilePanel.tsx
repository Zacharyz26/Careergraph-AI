import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingState } from "@/components/ui/LoadingState";
import type { CandidateProfile } from "@/lib/types";

export function CandidateProfilePanel({
  profile,
  isLoading = false,
  error = null,
  compact = false,
}: {
  profile: CandidateProfile | null;
  isLoading?: boolean;
  error?: string | null;
  compact?: boolean;
}) {
  if (!profile) {
    return (
      <section className={`card result-card${compact ? " result-card--compact" : ""}`}>
        <div className="card-heading">
          <div>
            <span className="eyebrow">Evidence profile</span>
            <h2>Building your career evidence</h2>
            <p>CareerGraph is organizing the resume into reviewable strengths, skills, and proof points.</p>
          </div>
        </div>
        {error ? <ErrorMessage message={error} /> : null}
        {isLoading ? (
          <LoadingState
            detail="This may take up to 60 seconds."
            label="Building your evidence profile..."
            stages={[
              "Reading skills, projects, education, and experience.",
              "Separating verified facts from possible positioning.",
              "Preparing a concise profile summary for the workspace.",
            ]}
          />
        ) : null}
      </section>
    );
  }

  const name = profile.basic_info.full_name || "Candidate profile";
  const headline =
    profile.basic_info.headline ||
    profile.inferred_target_roles[0]?.role ||
    "Evidence-based professional profile";

  return (
    <section className={`card result-card${compact ? " result-card--compact" : ""}`}>
      {error ? <ErrorMessage message={error} /> : null}
      {isLoading ? (
        <LoadingState
          compact
          detail="This may take up to 60 seconds. Your current profile remains available below."
          label="Refreshing your evidence profile..."
          stages={[
            "Refreshing skills, roles, and project evidence.",
            "Rechecking profile strengths against resume facts.",
            "Keeping the existing profile visible while the update finishes.",
          ]}
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
          <span className="eyebrow">Evidence profile</span>
          <h2>{name}</h2>
          <p>{headline}</p>
        </div>
      </div>

      <div className="profile-grid">
        <ProfileSection title="Core skill signals">
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

        <ProfileSection title="Strongest profile signals">
          {profile.strengths.length ? (
            <ul className="clean-list">
              {profile.strengths.slice(0, compact ? 3 : 4).map((strength) => (
                <li key={strength}>{strength}</li>
              ))}
            </ul>
          ) : (
            <p className="empty-copy">No explicit strengths were extracted.</p>
          )}
        </ProfileSection>
      </div>

      <div className="profile-stats">
        <Stat value={profile.experience.length} label="Experience" />
        <Stat value={profile.projects.length} label="Projects" />
        <Stat value={profile.education.length} label="Education" />
        <Stat value={profile.certifications.length} label="Certifications" />
      </div>

      {compact ? null : (
        <details className="disclosure">
          <summary>View detailed profile data</summary>
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
