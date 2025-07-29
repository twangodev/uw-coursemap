export { BaseSegment } from './base.ts';
export { CreditsSegment } from './credits.ts';
export { PrerequisitesSegment } from './prerequisites.ts';
export { StatisticsSegment } from './statistics.ts';
export { InstructorsSegment } from './instructors.ts';
export { AttributesSegment } from './attributes.ts';
export { ScheduleSegment } from './schedule.ts';

import type { BaseSegment } from './base.ts';
import { CreditsSegment } from './credits.ts';
import { PrerequisitesSegment } from './prerequisites.ts';
import { StatisticsSegment } from './statistics.ts';
import { InstructorsSegment } from './instructors.ts';
import { AttributesSegment } from './attributes.ts';
import { ScheduleSegment } from './schedule.ts';
import type { DescriptionContext } from '../types.ts';

export const segmentRegistry: Record<string, new (context: DescriptionContext) => BaseSegment> = {
  credits: CreditsSegment,
  prerequisites: PrerequisitesSegment,
  statistics: StatisticsSegment,
  instructors: InstructorsSegment,
  attributes: AttributesSegment,
  schedule: ScheduleSegment
};