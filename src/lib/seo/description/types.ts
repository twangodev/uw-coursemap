import type { Course } from "$lib/types/course.ts";
import type { FullInstructorInformation } from "$lib/types/instructor.ts";

export interface DescriptionContext {
  course: Course;
  instructors: FullInstructorInformation[];
  selectedTermId?: string;
  locale?: string;
  targetAudience?: 'prospective-students' | 'current-students' | 'general';
  style?: 'concise' | 'detailed' | 'engaging';
}

export interface DescriptionSegment {
  type: string;
  content: string;
  priority: number;
  metadata?: Record<string, any>;
}

export interface SegmentConfig {
  type: string;
  enabled: boolean;
  priority: number;
  maxLength?: number;
  minDataPoints?: number;
  template?: string;
}

export interface StyleConfig {
  tone: 'formal' | 'informative' | 'engaging' | 'concise';
  maxLength: number;
  minLength?: number;
  sentenceStructure: 'simple' | 'varied' | 'complex';
  transitions?: string[];
}

export interface GenerationRules {
  deduplication: boolean;
  grammarCheck: boolean;
  seoOptimization: boolean;
  keywordDensity?: number;
  requiredKeywords?: string[];
}

export interface VariantConfig {
  id: string;
  name?: string;
  maxSegments?: number;
  maxLength: number;
  minLength?: number;
  style?: string;
  segments?: string[];
}

export interface DescriptionConfig {
  segments: SegmentConfig[];
  styles: StyleConfig;
  rules: GenerationRules;
  variants?: VariantConfig[];
}

export interface GenerationOptions {
  type?: 'meta' | 'social' | 'catalog' | 'email' | 'default';
  variant?: string;
  config?: Partial<DescriptionConfig>;
  validationRules?: ValidationRules;
}

export interface ValidationRules {
  maxLength: number;
  minLength?: number;
  requiredKeywords?: string[];
  minReadabilityScore?: number;
  allowedCharacters?: RegExp;
}

export interface ValidationIssue {
  type: 'error' | 'warning' | 'info';
  message: string;
  field?: string;
}

export interface ValidationResult {
  isValid: boolean;
  issues: ValidationIssue[];
}

export type DescriptionType = 'meta' | 'social' | 'catalog' | 'email' | 'default';

export interface CachedDescription {
  description: string;
  timestamp: number;
  metadata?: Record<string, any>;
}