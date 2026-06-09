export function formatScore(score: number | undefined): string {
  return score === undefined ? "Pending" : `${Math.round(score)}%`;
}
