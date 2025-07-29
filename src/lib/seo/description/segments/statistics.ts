import { BaseSegment } from './base.ts';
import type { DescriptionSegment } from '../types.ts';
import { calculateGradePointAverage, calculateCompletionRate, calculateARate } from '$lib/types/madgrades.ts';

export class StatisticsSegment extends BaseSegment {
  get type() { return 'statistics'; }
  get priority() { return 5; }
  
  private readonly MIN_DATA_POINTS = 50;
  private readonly HIGH_A_RATE_THRESHOLD = 0.3;
  
  isApplicable(): boolean {
    const gradeData = this.context.course.cumulative_grade_data;
    return !!(gradeData && gradeData.total >= this.MIN_DATA_POINTS);
  }
  
  generate(): DescriptionSegment | null {
    const gradeData = this.context.course.cumulative_grade_data;
    if (!gradeData || gradeData.total < this.MIN_DATA_POINTS) return null;
    
    const stats = this.calculateStats(gradeData);
    const content = this.formatStats(stats);
    
    if (!content) return null;
    
    return {
      type: this.type,
      content,
      priority: this.priority,
      metadata: stats
    };
  }
  
  private calculateStats(gradeData: any) {
    return {
      gpa: calculateGradePointAverage(gradeData),
      completionRate: calculateCompletionRate(gradeData),
      aRate: calculateARate(gradeData),
      totalStudents: gradeData.total
    };
  }
  
  private formatStats(stats: ReturnType<typeof this.calculateStats>): string {
    const parts: string[] = [];
    
    // GPA - always show if available
    if (stats.gpa !== null) {
      parts.push(`${stats.gpa.toFixed(2)}/4.0 avg GPA`);
    }
    
    // Completion rate - show if concerning (below 90%)
    if (stats.completionRate !== null && stats.completionRate < 0.9) {
      parts.push(`${Math.round(stats.completionRate * 100)}% pass rate`);
    }
    
    // A-rate - show if notably high
    if (stats.aRate !== null && stats.aRate > this.HIGH_A_RATE_THRESHOLD) {
      parts.push(`${Math.round(stats.aRate * 100)}% earn A/AB`);
    }
    
    // Format based on number of stats
    if (parts.length === 0) return '';
    if (parts.length === 1) return parts[0] + '.';
    if (parts.length === 2) return `${parts[0]}, ${parts[1]}.`;
    
    // For 3 parts, use more natural formatting
    return `${parts[0]} with ${parts[1]} and ${parts[2]}.`;
  }
}