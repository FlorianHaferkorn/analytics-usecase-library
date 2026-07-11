/**
 * Governance Approval Types — bracket lifecycle management.
 */

export type ApprovalStatus = 'draft' | 'review' | 'approved' | 'rejected' | 'deprecated';

export interface ApprovalRecord {
  bracket_id: string;
  project_id: string;
  status: ApprovalStatus;
  submitted_by: string | null;
  approved_by: string | null;
  justification: string | null;
  created_at: string;
  updated_at: string;
}

export type ApprovalAction = 'submit' | 'approve' | 'reject' | 'deprecate' | 'reopen';

/** Valid status transitions. */
export const VALID_TRANSITIONS: Record<ApprovalStatus, ApprovalAction[]> = {
  draft: ['submit'],
  review: ['approve', 'reject'],
  approved: ['deprecate', 'reopen'],
  rejected: ['reopen'],
  deprecated: ['reopen'],
};
