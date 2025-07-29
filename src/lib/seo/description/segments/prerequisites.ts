import { BaseSegment } from './base.ts';
import type { DescriptionSegment } from '../types.ts';

export class PrerequisitesSegment extends BaseSegment {
  get type() { return 'prerequisites'; }
  get priority() { return 3; }
  
  isApplicable(): boolean {
    const prereqs = this.context.course.prerequisites?.prerequisites_text;
    return !!(prereqs && prereqs !== 'None');
  }
  
  generate(): DescriptionSegment | null {
    const prereqs = this.context.course.prerequisites?.prerequisites_text;
    if (!prereqs || prereqs === 'None') return null;
    
    // Clean up prerequisites text
    const cleanedPrereqs = prereqs
      .replace(/\s+/g, ' ')
      .trim()
      .replace(/\.$/, ''); // Remove trailing period if present
    
    return {
      type: this.type,
      content: `Prerequisites: ${cleanedPrereqs}.`,
      priority: this.priority,
      metadata: { prerequisites: cleanedPrereqs }
    };
  }
}