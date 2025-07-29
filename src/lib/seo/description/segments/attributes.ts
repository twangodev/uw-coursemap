import { BaseSegment } from './base.ts';
import type { DescriptionSegment } from '../types.ts';

export class AttributesSegment extends BaseSegment {
  get type() { return 'attributes'; }
  get priority() { return 7; }
  
  isApplicable(): boolean {
    const termData = this.getLatestTermData();
    const enrollment = termData?.enrollment_data;
    return !!(enrollment?.general_education || enrollment?.ethnic_studies);
  }
  
  generate(): DescriptionSegment | null {
    const termData = this.getLatestTermData();
    const enrollment = termData?.enrollment_data;
    if (!enrollment) return null;
    
    const attributes: string[] = [];
    if (enrollment.general_education) attributes.push('General Education');
    if (enrollment.ethnic_studies) attributes.push('Ethnic Studies');
    
    if (attributes.length === 0) return null;
    
    const content = attributes.length === 1
      ? `Fulfills ${attributes[0]} requirement.`
      : `Fulfills ${attributes.join(' and ')} requirements.`;
    
    return {
      type: this.type,
      content,
      priority: this.priority,
      metadata: { attributes }
    };
  }
}