import { getReasonPhrase } from "http-status-codes";

type ErrorCopy = { title: string; description: string; retry: boolean };
const messages: Record<number, ErrorCopy> = {
  400: {
    title: "That request didn’t quite work.",
    description: "Try searching again, or start from the course directory.",
    retry: false,
  },
  403: {
    title: "This page isn’t available to you.",
    description: "You can still explore the public course directory.",
    retry: false,
  },
  404: {
    title: "A little off course.",
    description:
      "We couldn’t find this page. Your next class is still out there.",
    retry: false,
  },
  410: {
    title: "This page has moved on.",
    description:
      "This page is no longer available. Search the current course directory instead.",
    retry: false,
  },
  429: {
    title: "Let’s take a short break.",
    description:
      "There have been too many requests. Wait a moment, then try again.",
    retry: true,
  },
  503: {
    title: "Back after a short break.",
    description:
      "This part of uwcourses is temporarily unavailable. Please try again shortly.",
    retry: true,
  },
};
export function errorPresentation(status: number) {
  let label = "Unexpected error";
  try {
    label = getReasonPhrase(status);
  } catch {
    /* Nonstandard status. */
  }
  return {
    status,
    label,
    ...(messages[status] ?? {
      title: "We lost the thread.",
      description:
        "Something went wrong loading this page. Try again, or head back to the course directory.",
      retry: status >= 500,
    }),
  };
}
