/**
 * Lightweight intersection observer action for scroll-triggered animations
 */

interface InViewOptions {
  threshold?: number;
  rootMargin?: string;
  once?: boolean;
}

export function inView(
  node: HTMLElement,
  options: InViewOptions = {}
) {
  const {
    threshold = 0.3,
    rootMargin = '0px',
    once = false
  } = options;

  let isInView = false;
  let hasAnimated = false;

  // Create two observers for hysteresis effect
  // Enter observer triggers when element is more visible
  const enterObserver = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting && !isInView && (!once || !hasAnimated)) {
        isInView = true;
        node.classList.add('in-view');
        hasAnimated = true;
        
        node.dispatchEvent(new CustomEvent('inview', { 
          detail: { isIntersecting: true } 
        }));
        
        if (once) {
          enterObserver.disconnect();
          exitObserver.disconnect();
        }
      }
    },
    { threshold, rootMargin }
  );

  // Exit observer triggers when element is much less visible
  // Using a lower threshold (10% visibility) to create hysteresis
  const exitObserver = new IntersectionObserver(
    ([entry]) => {
      if (!entry.isIntersecting && isInView && !once) {
        isInView = false;
        node.classList.remove('in-view');
        
        node.dispatchEvent(new CustomEvent('inview', { 
          detail: { isIntersecting: false } 
        }));
      }
    },
    { 
      threshold: 0.1, // Exit when less than 10% visible
      rootMargin: '-10%' // Additional margin to ensure element is well out of view
    }
  );

  enterObserver.observe(node);
  exitObserver.observe(node);

  return {
    destroy() {
      enterObserver.disconnect();
      exitObserver.disconnect();
    }
  };
}