import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingState } from "@/components/ui/LoadingState";
import type { CandidateProfile } from "@/lib/types";

export function CandidateProfilePanel({
  profile,
  isLoading = false,
  error = null,
}: {
  profile: CandidateProfile | null;
  isLoading?: boolean;
  error?: string | null;
}) {
  if (!profile) {
    return (
      <section className="card result-card">
        <div className="card-heading">
          <div>
            <span className="eyebrow">Candidate profile</span>
            <h2>Building your structured profile</h2>
            <p>Your extracted resume remains grounded in the source document.</p>
          </div>
        </div>
        {error ? <ErrorMessage message={error} /> : null}
        {isLoading ? (
          <LoadingState
            detail="This may take up to 60 seconds."
            label="Parsing your resume into a structured profile..."
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
    <section className="card result-card">
      {error ? <ErrorMessage message={error} /> : null}
      {isLoading ? (
        <LoadingState
          compact
          detail="This may take up to 60 seconds. Your current profile remains available below."
          label="Parsing your resume into a structured profile..."
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
          <span className="eyebrow">Candidate profile</span>
          <h2>{name}</h2>
          <p>{headline}</p>
        </div>
      </div>

      <div className="profile-grid">
        <ProfileSection title="Core skills">
          <div className="tag-list">
            {profile.skills.flatMap((group) =>
              group.skills.map((skill) => (
                <span className="tag" key={`${group.category}-${skill}`}>
                  {skill}
                </span>
              )),
            )}
          </div>
        </ProfileSection>

        <ProfileSection title="Strengths">
          {profile.strengths.length ? (
            <ul className="clean-list">
              {profile.strengths.slice(0, 4).map((strength) => (
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

      <details className="disclosure">
        <summary>View structured profile JSON</summary>
        <pre>{JSON.stringify(profile, null, 2)}</pre>
      </details>
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
