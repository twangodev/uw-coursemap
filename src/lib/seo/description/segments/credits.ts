import { BaseSegment } from './base.ts';
import type { DescriptionSegment } from '../types.ts';

export class CreditsSegment extends BaseSegment {
  get type() { return 'credits'; }
  get priority() { return 2; }
  
  isApplicable(): boolean {
    const termData = this.getLatestTermData();
    return !!(termData?.enrollment_data?.credit_count);
  }
  
  generate(): DescriptionSegment | null {
    const termData = this.getLatestTermData();
    if (!termData?.enrollment_data?.credit_count) return null;
    
    const [minCredits, maxCredits] = termData.enrollment_data.credit_count;
    
    const content = minCredits === maxCredits
      ? `This ${minCredits}-credit course`
      : `This ${minCredits}-${maxCredits} credit course`;
    
    return {
      type: this.type,
      content,
      priority: this.priority,
      metadata: { minCredits, maxCredits }
    };
  }
}