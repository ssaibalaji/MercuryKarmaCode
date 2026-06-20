export type UserRole = 'student' | 'examiner' | 'coach';

export interface User {
  id: number;
  email: string;
  fullName: string | null;
  role: UserRole;
  isActive: boolean;
  isVerified: boolean;
  createdAt: string;
}

export type SubmissionSyncStatus = 'pending' | 'synced' | 'error';

export interface Submission {
  id: number;
  userId: number;
  studentName: string;
  studentEmail: string;
  assignmentName: string;
  githubRepoUrl: string;
  syncStatus: SubmissionSyncStatus;
  submittedAt: string;
}

export type EvaluationStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Evaluation {
  id: number;
  submissionId: number;
  aiRoastText: string;
  aiScore: number;
  staticAnalysisReport: Record<string, unknown>;
  staticAnalysisScore: number;
  overallScore: number;
  status: EvaluationStatus;
  evaluatedAt: string;
}

export interface DashboardStats {
  totalSubmissions: number;
  pendingEvaluations: number;
  completedEvaluations: number;
  failedEvaluations: number;
  averageOverallScore: number | null;
}

export interface ScoreDistributionBucket {
  range: string;
  count: number;
}

export interface SubmissionsOverTimePoint {
  date: string;
  count: number;
}
