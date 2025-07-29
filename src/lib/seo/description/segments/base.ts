import type { DescriptionContext, DescriptionSegment } from '../types.ts';

export abstract class BaseSegment {
  protected context: DescriptionContext;
  
  constructor(context: DescriptionContext) {
    this.context = context;
  }
  
  abstract get type(): string;
  abstract get priority(): number;
  abstract isApplicable(): boolean;
  abstract generate(): DescriptionSegment | null;
  
  protected getLatestTermId(): string | null {
    const termIds = Object.keys(this.context.course.term_data).sort().reverse();
    return termIds[0] || null;
  }
  
  protected getLatestTermData() {
    const termId = this.getLatestTermId();
    return termId ? this.context.course.term_data[termId] : null;
  }
}