import "server-only";
import { createHash } from "node:crypto";
import type { PublicReview } from "@/lib/api";
import type { Lesson } from "@/lib/lessons";

/**
 * Fingerprint of a lesson's content: the SHA-256 of its full text and links.
 * A legal review is pinned to it, so any edit to the lesson makes the review
 * no longer apply until the lesson is reviewed again.
 */
export function lessonFingerprint(lesson: Lesson): string {
  return createHash("sha256").update(JSON.stringify(lesson)).digest("hex");
}

export type ReviewState =
  | { kind: "reviewed"; date: string }
  | { kind: "changed_since_review"; date: string }
  | { kind: "pending" };

/** Reviewed only when the latest decision is an approval of exactly the current content. */
export function reviewState(review: PublicReview | undefined, fingerprint: string | null): ReviewState {
  if (!review || review.decision !== "approved") return { kind: "pending" };
  if (fingerprint !== null && review.fingerprint === fingerprint) {
    return { kind: "reviewed", date: review.reviewed_at };
  }
  return { kind: "changed_since_review", date: review.reviewed_at };
}
