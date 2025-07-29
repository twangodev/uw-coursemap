import { BaseSegment } from './base.ts';
import type { DescriptionSegment } from '../types.ts';

export class ScheduleSegment extends BaseSegment {
  get type() { return 'schedule'; }
  get priority() { return 4; }
  
  isApplicable(): boolean {
    const termData = this.getLatestTermData();
    return !!(termData?.enrollment_data?.typically_offered);
  }
  
  generate(): DescriptionSegment | null {
    const termData = this.getLatestTermData();
    const typicallyOffered = termData?.enrollment_data?.typically_offered;
    
    if (!typicallyOffered) return null;
    
    const content = this.formatSchedule(typicallyOffered);
    
    return {
      type: this.type,
      content,
      priority: this.priority,
      metadata: { typicallyOffered }
    };
  }
  
  private formatSchedule(schedule: string): string {
    // Handle common patterns
    const scheduleMap: Record<string, string> = {
      'Fall': 'Offered every Fall',
      'Spring': 'Offered every Spring',
      'Summer': 'Offered in Summer',
      'Fall and Spring': 'Offered Fall and Spring',
      'Every semester': 'Offered every semester',
      'Occasionally': 'Offered occasionally',
      'Varies': 'Schedule varies by year'
    };
    
    return (scheduleMap[schedule] || `Typically offered ${schedule}`) + '.';
  }
}