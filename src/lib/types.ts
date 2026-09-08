export type RecordData = Record<string, any>;
export interface CourseCard {
  course_uid: string;
  course_id: string;
  title: string;
  credits_min: number | null;
  credits_max: number | null;
  gpa: number | null;
}
export interface Status {
  revision: string;
  repository: string;
  observed_at: string;
  built_at: string;
  term: string;
  terms: string[];
  courses: number;
  current_instructors: number;
  departments: { subject: string; count: number }[];
}
export interface Citation {
  type: string;
  source_url?: string;
  source_review_id?: string;
  instructor_name?: string;
  review_date?: string;
  term_id?: string;
  [key: string]: unknown;
}
export interface Claim {
  text: string;
  citations?: Citation[];
}
export interface RequirementNode {
  id: string;
  kind: string;
  children: string[];
  condition?: string;
  evidence?: string;
  course?: {
    subjects: string[];
    course_number: number;
    minimum_grade?: string;
    timing?: string;
  };
}
export interface Requirements {
  root: string;
  nodes: RequirementNode[];
  status?: string;
  notes?: string[];
}
