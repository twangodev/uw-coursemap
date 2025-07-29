import type { DescriptionConfig, VariantConfig } from './types.ts';

export const defaultDescriptionConfig: DescriptionConfig = {
  segments: [
    { type: 'base', enabled: true, priority: 1, maxLength: 200 },
    { type: 'credits', enabled: true, priority: 2, maxLength: 30 },
    { type: 'prerequisites', enabled: true, priority: 3, maxLength: 100 },
    { type: 'schedule', enabled: true, priority: 4, maxLength: 50 },
    { type: 'statistics', enabled: true, priority: 5, minDataPoints: 50, maxLength: 80 },
    { type: 'instructors', enabled: true, priority: 6, maxLength: 100 },
    { type: 'attributes', enabled: true, priority: 7, maxLength: 60 },
    { type: 'related', enabled: true, priority: 8, maxLength: 50 }
  ],
  styles: {
    tone: 'informative',
    maxLength: 320,
    minLength: 120,
    sentenceStructure: 'varied',
    transitions: ['Additionally', 'Furthermore', 'Students also']
  },
  rules: {
    deduplication: true,
    grammarCheck: true,
    seoOptimization: true,
    keywordDensity: 0.02,
    requiredKeywords: []
  }
};

export const descriptionVariants: Record<string, VariantConfig> = {
  meta: {
    id: 'meta',
    name: 'Meta Description',
    maxLength: 160,
    minLength: 120,
    maxSegments: 4,
    segments: ['base', 'credits', 'statistics', 'instructors']
  },
  social: {
    id: 'social',
    name: 'Social Media',
    maxLength: 280,
    minLength: 100,
    style: 'engaging',
    segments: ['base', 'statistics', 'instructors', 'attributes']
  },
  catalog: {
    id: 'catalog',
    name: 'Course Catalog',
    maxLength: 500,
    minLength: 200,
    segments: ['base', 'credits', 'prerequisites', 'schedule', 'attributes']
  },
  email: {
    id: 'email',
    name: 'Email Description',
    maxLength: 200,
    minLength: 80,
    style: 'concise',
    segments: ['base', 'credits', 'schedule']
  },
  mobile: {
    id: 'mobile',
    name: 'Mobile Description',
    maxLength: 120,
    minLength: 80,
    maxSegments: 3,
    segments: ['base', 'credits', 'statistics']
  }
};

// Template configurations for different segment types
export const segmentTemplates = {
  credits: {
    single: "This {{credits}}-credit course",
    range: "This {{minCredits}}-{{maxCredits}} credit course",
    withLevel: "This {{level}} {{credits}}-credit course"
  },
  prerequisites: {
    single: "Prerequisite: {{prerequisite}}",
    multiple: "Prerequisites: {{prerequisites}}",
    none: "No prerequisites required"
  },
  schedule: {
    regular: "Offered {{schedule}}",
    specific: "Offered in {{terms}}",
    lastTaught: "Last taught {{term}}"
  },
  statistics: {
    gpa: "Average GPA: {{gpa}}/4.0",
    completion: "{{rate}}% completion rate",
    combined: "{{gpa}}/4.0 avg GPA, {{completion}}% pass rate",
    aRate: "{{rate}}% earn A/AB"
  },
  instructors: {
    single: "Taught by {{instructor}}",
    multiple: "Instructors include {{instructors}}",
    rated: "Taught by highly-rated {{instructors}}"
  },
  attributes: {
    single: "Fulfills {{attribute}} requirement",
    multiple: "Fulfills {{attributes}} requirements",
    withLevel: "{{level}} course fulfilling {{attributes}}"
  }
};

// SEO-optimized keyword patterns
export const keywordPatterns = {
  courseCode: ['{{subject}} {{number}}', '{{subject}}{{number}}', '{{code}}'],
  level: ['{{level}} course', '{{level}} level', '{{level}}'],
  subject: ['{{subject}}', '{{department}}', '{{school}}'],
  university: ['UW-Madison', 'University of Wisconsin', 'UW Madison', 'Wisconsin']
};

// Character limits for different platforms
export const platformLimits = {
  google: { title: 60, description: 160 },
  facebook: { title: 40, description: 300 },
  twitter: { total: 280 },
  mobile: { title: 40, description: 120 }
};

export function getConfigForVariant(variantId: string): DescriptionConfig {
  const variant = descriptionVariants[variantId];
  if (!variant) {
    return defaultDescriptionConfig;
  }

  const config = { ...defaultDescriptionConfig };
  
  // Apply variant-specific settings
  if (variant.maxLength) {
    config.styles.maxLength = variant.maxLength;
  }
  if (variant.minLength) {
    config.styles.minLength = variant.minLength;
  }
  if (variant.segments) {
    config.segments = config.segments
      .filter(s => variant.segments!.includes(s.type))
      .sort((a, b) => variant.segments!.indexOf(a.type) - variant.segments!.indexOf(b.type));
  }
  if (variant.style) {
    config.styles.tone = variant.style as any;
  }

  return config;
}