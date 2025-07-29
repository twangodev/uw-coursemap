import type { Course } from '$lib/types/course.ts';
import type { FullInstructorInformation } from '$lib/types/instructor.ts';
import type { 
  DescriptionContext, 
  DescriptionSegment, 
  DescriptionConfig,
  GenerationOptions
} from './types.ts';
import { segmentRegistry } from './segments/index.ts';
import { defaultDescriptionConfig, getConfigForVariant } from './config.ts';
import { DescriptionComposer } from './composer.ts';

export class CourseDescriptionBuilder {
  private context: DescriptionContext;
  private config: DescriptionConfig;
  private segments: DescriptionSegment[] = [];
  
  constructor(
    course: Course, 
    instructors: FullInstructorInformation[],
    options?: GenerationOptions
  ) {
    this.context = {
      course,
      instructors,
      selectedTermId: options?.config?.segments?.[0]?.type || undefined,
      locale: 'en-US',
      targetAudience: 'prospective-students',
      style: options?.config?.styles?.tone === 'engaging' ? 'engaging' : 'concise'
    };
    
    this.config = this.resolveConfig(options);
  }
  
  private resolveConfig(options?: GenerationOptions): DescriptionConfig {
    if (options?.variant) {
      return getConfigForVariant(options.variant);
    }
    
    if (options?.config) {
      return {
        ...defaultDescriptionConfig,
        ...options.config,
        segments: options.config.segments || defaultDescriptionConfig.segments,
        styles: { ...defaultDescriptionConfig.styles, ...options.config.styles },
        rules: { ...defaultDescriptionConfig.rules, ...options.config.rules }
      };
    }
    
    return defaultDescriptionConfig;
  }
  
  build(): string {
    // Generate segments based on configuration
    this.generateSegments();
    
    // Use composer to create final description
    const composer = new DescriptionComposer(this.segments, this.context, this.config);
    return composer.compose();
  }
  
  private generateSegments(): void {
    // Add base description first if available
    if (this.context.course.description) {
      this.segments.push({
        type: 'base',
        content: this.context.course.description,
        priority: 1
      });
    }
    
    // Generate configured segments
    for (const segmentConfig of this.config.segments) {
      if (!segmentConfig.enabled) continue;
      
      const SegmentClass = segmentRegistry[segmentConfig.type];
      if (!SegmentClass) continue;
      
      const segment = new SegmentClass(this.context);
      if (segment.isApplicable()) {
        const generated = segment.generate();
        if (generated) {
          this.segments.push(generated);
        }
      }
    }
  }
  
  // Fluent API methods for manual building if needed
  addSegment(type: string): this {
    const SegmentClass = segmentRegistry[type];
    if (SegmentClass) {
      const segment = new SegmentClass(this.context);
      if (segment.isApplicable()) {
        const generated = segment.generate();
        if (generated) {
          this.segments.push(generated);
        }
      }
    }
    return this;
  }
  
  withConfig(config: Partial<DescriptionConfig>): this {
    this.config = {
      ...this.config,
      ...config,
      styles: { ...this.config.styles, ...config.styles },
      rules: { ...this.config.rules, ...config.rules }
    };
    return this;
  }
}