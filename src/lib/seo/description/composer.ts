import type { 
  DescriptionContext, 
  DescriptionSegment, 
  DescriptionConfig 
} from './types.ts';

export class DescriptionComposer {
  private segments: DescriptionSegment[];
  private context: DescriptionContext;
  private config: DescriptionConfig;
  
  constructor(
    segments: DescriptionSegment[], 
    context: DescriptionContext,
    config: DescriptionConfig
  ) {
    this.segments = segments;
    this.context = context;
    this.config = config;
  }
  
  compose(): string {
    const sortedSegments = this.prioritizeSegments();
    const selectedSegments = this.selectSegments(sortedSegments);
    const processedContent = this.processSegments(selectedSegments);
    return this.finalizeDescription(processedContent);
  }
  
  private prioritizeSegments(): DescriptionSegment[] {
    return [...this.segments].sort((a, b) => a.priority - b.priority);
  }
  
  private selectSegments(segments: DescriptionSegment[]): DescriptionSegment[] {
    const selected: DescriptionSegment[] = [];
    let currentLength = 0;
    const maxLength = this.config.styles.maxLength;
    const buffer = 20; // Leave some room for punctuation and joining
    
    for (const segment of segments) {
      const segmentLength = segment.content.length;
      
      // Always include base description if it fits
      if (segment.type === 'base' && currentLength + segmentLength <= maxLength - buffer) {
        selected.push(segment);
        currentLength += segmentLength + 2; // +2 for space and punctuation
        continue;
      }
      
      // Check if adding this segment would exceed limit
      if (currentLength + segmentLength + 2 > maxLength - buffer) {
        // If we have room for a partial segment and it's important, consider truncating
        if (segment.priority <= 3 && currentLength < maxLength * 0.7) {
          const availableSpace = maxLength - currentLength - buffer;
          if (availableSpace > 50) { // Only truncate if we have reasonable space
            const truncated = this.truncateSegment(segment, availableSpace);
            if (truncated) {
              selected.push(truncated);
              currentLength += truncated.content.length + 2;
            }
          }
        }
        break;
      }
      
      selected.push(segment);
      currentLength += segmentLength + 2;
    }
    
    return selected;
  }
  
  private truncateSegment(segment: DescriptionSegment, maxLength: number): DescriptionSegment | null {
    if (segment.content.length <= maxLength) return segment;
    
    // Don't truncate certain segment types
    if (['statistics', 'credits', 'attributes'].includes(segment.type)) {
      return null;
    }
    
    // Find a good truncation point
    const truncated = segment.content.substring(0, maxLength - 3);
    const lastPeriod = truncated.lastIndexOf('.');
    const lastComma = truncated.lastIndexOf(',');
    const lastSpace = truncated.lastIndexOf(' ');
    
    let cutPoint = Math.max(lastPeriod, lastComma, lastSpace);
    if (cutPoint < maxLength * 0.5) {
      cutPoint = lastSpace;
    }
    
    if (cutPoint <= 0) return null;
    
    return {
      ...segment,
      content: truncated.substring(0, cutPoint) + '...'
    };
  }
  
  private processSegments(segments: DescriptionSegment[]): string[] {
    const processed: string[] = [];
    
    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      let content = segment.content;
      
      // Ensure proper sentence ending
      if (!content.match(/[.!?]$/)) {
        content += '.';
      }
      
      // Add transitions for better flow (but not for base description)
      if (i > 0 && segment.type !== 'base' && this.shouldAddTransition(i, segments)) {
        const transition = this.selectTransition(segment.type, i);
        if (transition) {
          content = `${transition} ${content.charAt(0).toLowerCase()}${content.slice(1)}`;
        }
      }
      
      processed.push(content);
    }
    
    return processed;
  }
  
  private shouldAddTransition(index: number, segments: DescriptionSegment[]): boolean {
    // Don't add transitions if we're being concise
    if (this.config.styles.tone === 'concise') return false;
    
    // Don't add transition after very short segments
    if (index > 0 && segments[index - 1].content.length < 30) return false;
    
    // Add transitions strategically
    return index === 2 || index === 4;
  }
  
  private selectTransition(segmentType: string, index: number): string {
    const transitions = this.config.styles.transitions || [];
    if (transitions.length === 0) return '';
    
    // Select transition based on segment type and position
    const typeTransitions: Record<string, string[]> = {
      statistics: ['Additionally,', 'Notably,'],
      instructors: ['The course is', 'Students learn from'],
      attributes: ['This course also', 'Furthermore, it'],
      schedule: ['The course is', 'Classes are']
    };
    
    const specific = typeTransitions[segmentType];
    if (specific && specific.length > 0) {
      return specific[index % specific.length];
    }
    
    return transitions[index % transitions.length];
  }
  
  private finalizeDescription(segments: string[]): string {
    let description = segments.join(' ');
    
    // Clean up spacing and punctuation
    description = description
      .replace(/\s+/g, ' ')
      .replace(/\s+([.,!?])/g, '$1')
      .replace(/\.+/g, '.')
      .trim();
    
    // Ensure it ends with proper punctuation
    if (!description.match(/[.!?]$/)) {
      description += '.';
    }
    
    // Apply final SEO optimizations if enabled
    if (this.config.rules.seoOptimization) {
      description = this.optimizeForSEO(description);
    }
    
    // Final length check
    if (description.length > this.config.styles.maxLength) {
      description = this.hardTruncate(description, this.config.styles.maxLength);
    }
    
    return description;
  }
  
  private optimizeForSEO(description: string): string {
    // Ensure important keywords appear early
    const courseCode = `${this.context.course.course_reference.subjects[0]} ${this.context.course.course_reference.course_number}`;
    
    if (!description.includes(courseCode) && description.length < this.config.styles.maxLength - courseCode.length - 5) {
      // Try to naturally include the course code if it's missing
      description = `${courseCode}: ${description}`;
    }
    
    return description;
  }
  
  private hardTruncate(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    
    const truncated = text.substring(0, maxLength - 3);
    const lastSpace = truncated.lastIndexOf(' ');
    
    if (lastSpace > maxLength * 0.8) {
      return truncated.substring(0, lastSpace) + '...';
    }
    
    return truncated + '...';
  }
}