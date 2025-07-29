import { BaseSegment } from './base.ts';
import type { DescriptionSegment } from '../types.ts';

export class InstructorsSegment extends BaseSegment {
  get type() { return 'instructors'; }
  get priority() { return 6; }
  
  private readonly MIN_RATING = 3.5;
  private readonly MAX_INSTRUCTORS = 3;
  
  isApplicable(): boolean {
    return this.getTopInstructors().length > 0;
  }
  
  generate(): DescriptionSegment | null {
    const topInstructors = this.getTopInstructors();
    if (topInstructors.length === 0) return null;
    
    const content = this.formatInstructors(topInstructors);
    
    return {
      type: this.type,
      content,
      priority: this.priority,
      metadata: { 
        instructors: topInstructors,
        count: topInstructors.length 
      }
    };
  }
  
  private getTopInstructors(): string[] {
    return this.context.instructors
      .filter(i => i.rmp_data && i.rmp_data.average_rating >= this.MIN_RATING)
      .sort((a, b) => (b.rmp_data?.average_rating || 0) - (a.rmp_data?.average_rating || 0))
      .slice(0, this.MAX_INSTRUCTORS)
      .map(i => i.name);
  }
  
  private formatInstructors(instructors: string[]): string {
    if (instructors.length === 0) return '';
    
    const lastName = (name: string) => {
      const parts = name.split(' ');
      return parts[parts.length - 1];
    };
    
    // Use last names for brevity
    const lastNames = instructors.map(lastName);
    
    if (lastNames.length === 1) {
      return `Taught by highly-rated Prof. ${lastNames[0]}.`;
    }
    
    if (lastNames.length === 2) {
      return `Taught by highly-rated professors ${lastNames[0]} and ${lastNames[1]}.`;
    }
    
    // For 3+ instructors
    const allButLast = lastNames.slice(0, -1).join(', ');
    const last = lastNames[lastNames.length - 1];
    return `Taught by highly-rated professors including ${allButLast}, and ${last}.`;
  }
}