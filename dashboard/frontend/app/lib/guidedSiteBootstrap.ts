/**
 * Product Identity v1.0 — Vector workspace entry (no goal picker).
 */

import {
  GUIDED_GOAL_WEBSITE_ID,
  loadGuidedCommerce,
  selectGuidedGoal,
  type GuidedCommerceState,
} from "./guidedCommerce";

/** Start website project silently — Vector leads, not a form menu. */
export function initVectorWorkspace(): GuidedCommerceState {
  const prev = loadGuidedCommerce();
  if (prev.goalId) return prev;
  return selectGuidedGoal(GUIDED_GOAL_WEBSITE_ID);
}
